from typing import Dict, Set, List
from sqlglot import parse_one, exp
from app.settings import settings
MAX_LIMIT = settings.MAX_LIMIT
DEFAULT_LIMIT = settings.DEFAULT_LIMIT

# ----- Allowed schema (single-table MVP) -----
ALLOWED_SCHEMA: Dict[str, Set[str]] = {
    "pitches": {"id", "game_date", "pitcher", "batter", "pitch_type", "result"}
}

class ValidationError(Exception):
    pass

ALLOWED_AGG_FUNCS = (exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max)

def _strip_trailing_semicolon(sql: str) -> str:
    return sql.strip().rstrip(";").strip()

def validate_and_rewrite_sql(sql: str) -> str:
    """
    Safe subset:
      - Single SELECT (WITH ok)
      - Single table from ALLOWED_SCHEMA
      - Columns must be allowed
      - Aggregates allowed: COUNT, SUM, AVG, MIN, MAX
      - If aggregates + non-agg columns appear together -> require GROUP BY on those columns
      - GROUP BY columns must be allowed columns (no expressions)
      - ORDER BY allowed on columns, or allowed aggregates, or select aliases
      - No JOINs, subqueries, or other functions
      - LIMIT must be numeric and <= MAX_LIMIT; add DEFAULT_LIMIT if missing
      - Allow COUNT(*) only inside COUNT()
    """
    if not sql or not isinstance(sql, str):
        raise ValidationError("Empty SQL")

    sql = _strip_trailing_semicolon(sql)

    # Parse
    try:
        node = parse_one(sql, read="postgres")
    except Exception as e:
        raise ValidationError(f"Parse error: {e}")

    # Unwrap WITH -> SELECT
    select_node = node
    if isinstance(node, exp.With):
        if not isinstance(node.this, exp.Select):
            raise ValidationError("WITH must contain a SELECT")
        select_node = node.this

    if not isinstance(select_node, exp.Select):
        raise ValidationError("Only SELECT queries are allowed")

    # Disallow JOINs and subqueries for MVP
    if list(select_node.find_all(exp.Join)):
        raise ValidationError("JOINs are not allowed in the MVP")
    if list(select_node.find_all(exp.Subquery)):
        raise ValidationError("Subqueries are not allowed in the MVP")

    # Validate table usage (single table)
    tables = [t.name for t in select_node.find_all(exp.Table)]
    if not tables:
        raise ValidationError("Query must reference a table")
    if len(set(tables)) != 1:
        raise ValidationError("Only one table is allowed")
    table = tables[0]
    if table not in ALLOWED_SCHEMA:
        raise ValidationError(f"Table '{table}' is not allowed")
    allowed_cols = ALLOWED_SCHEMA[table]

    # Disallow any function that isn't an allowed aggregate
    for fn in select_node.find_all(exp.Func):
        if not isinstance(fn, ALLOWED_AGG_FUNCS):
            # COUNT, SUM, AVG, MIN, MAX are ok; everything else is not.
            raise ValidationError(f"Function '{fn.key.upper()}' is not allowed")

    # Star (*) must only appear inside COUNT(*)
    for star in select_node.find_all(exp.Star):
        if not star.find_ancestor(exp.Count):
            raise ValidationError("SELECT * is not allowed (only COUNT(*) is permitted)")

    # Collect select aliases (so ORDER BY can reference them)
    select_aliases: Set[str] = set()
    for proj in select_node.expressions:
        if isinstance(proj, exp.Alias) and proj.alias:
            select_aliases.add(proj.alias)

    # Helper: find non-aggregate columns appearing in SELECT list
    def nonagg_columns_in_projection() -> List[str]:
        nonagg_cols: List[str] = []
        for proj in select_node.expressions:
            # descend into each projection; collect Columns that do NOT have an aggregate ancestor
            for col in proj.find_all(exp.Column):
                if not (col.find_ancestor(exp.Count) or col.find_ancestor(exp.Sum)
                        or col.find_ancestor(exp.Avg) or col.find_ancestor(exp.Min)
                        or col.find_ancestor(exp.Max)):
                    nonagg_cols.append(col.name)
        return nonagg_cols

    # Validate every Column (anywhere) touches only allowed columns
    for col in select_node.find_all(exp.Column):
        if col.name not in allowed_cols:
            # allow aliases later for ORDER BY through separate rule
            raise ValidationError(f"Column '{col.name}' is not allowed on '{table}'")

    # Aggregates present?
    has_agg = any(isinstance(fn, ALLOWED_AGG_FUNCS) for fn in select_node.find_all(exp.Func))

    # GROUP BY validation when mixed select (agg + non-agg)
    group_expr = select_node.args.get("group")
    nonagg_cols = nonagg_columns_in_projection()

    if has_agg and nonagg_cols:
        if group_expr is None:
            raise ValidationError("GROUP BY required when selecting columns with aggregates")
        # group_expr.expressions should be simple columns
        group_cols: List[str] = []
        for g in group_expr.expressions:
            # We require plain columns in the GROUP BY
            gcols = list(g.find_all(exp.Column))
            if len(gcols) != 1:
                raise ValidationError("GROUP BY must use plain columns (no expressions)")
            gc = gcols[0].name
            if gc not in allowed_cols:
                raise ValidationError(f"GROUP BY column '{gc}' is not allowed")
            group_cols.append(gc)
        # All non-agg columns in SELECT must be grouped
        for c in nonagg_cols:
            if c not in group_cols:
                raise ValidationError(f"Column '{c}' must be included in GROUP BY")

    # ORDER BY validation: allow ordering by allowed column names, allowed aggregates, or select aliases
    order_expr = select_node.args.get("order")
    if order_expr is not None:
        for ordered in order_expr.expressions:  # each 'Ordered' item
            target = ordered.this
            if isinstance(target, exp.Column):
                name = target.name
                if (name not in allowed_cols) and (name not in select_aliases):
                    raise ValidationError(f"ORDER BY column '{name}' is not allowed")
            elif isinstance(target, ALLOWED_AGG_FUNCS):
                # ORDER BY COUNT(...), etc. OK
                pass
            else:
                # Disallow positional ORDER BY (e.g., ORDER BY 1) or arbitrary expressions in MVP
                raise ValidationError("ORDER BY must use columns, select aliases, or allowed aggregates")

    # LIMIT (add or clamp)
    limit_expr = select_node.args.get("limit")
    if limit_expr is None:
        select_node.set("limit", exp.Limit(this=exp.Literal.number(DEFAULT_LIMIT)))
    else:
        lit = limit_expr.this
        if not isinstance(lit, exp.Literal) or not lit.is_number:
            raise ValidationError("LIMIT must be a number")
        n = max(1, min(int(lit.name), MAX_LIMIT))
        limit_expr.set("this", exp.Literal.number(n))

    # Return normalized, safe SQL string
    safe_sql = select_node.sql(dialect="postgres")
    return safe_sql
