import re


# SQL operations that OpsIntel must never execute.
FORBIDDEN_KEYWORDS = {
    "ALTER",
    "CREATE",
    "DELETE",
    "DROP",
    "GRANT",
    "INSERT",
    "MERGE",
    "RENAME",
    "REVOKE",
    "TRUNCATE",
    "UPDATE",
}


class UnsafeQueryError(ValueError):
    """Raised when a SQL query violates OpsIntel read-only policy."""


def validate_sql(sql: str) -> str:
    """
    Validate SQL before execution.

    OpsIntel permits read-only queries beginning with SELECT, WITH,
    or EXPLAIN. Destructive or modifying SQL is rejected.
    """

    if not isinstance(sql, str):
        raise UnsafeQueryError("SQL query must be a string.")

    query = sql.strip()

    if not query:
        raise UnsafeQueryError("SQL query cannot be empty.")

    # Remove a single trailing semicolon for validation.
    normalized = query.rstrip(";").strip()

    # Reject multiple statements.
    if ";" in normalized:
        raise UnsafeQueryError(
            "Multiple SQL statements are not allowed."
        )

    # Only permit read-oriented statements.
    first_keyword = re.match(
        r"^\s*([A-Za-z]+)",
        normalized,
    )

    if not first_keyword:
        raise UnsafeQueryError(
            "Could not determine the SQL statement type."
        )

    statement_type = first_keyword.group(1).upper()

    if statement_type not in {"SELECT", "WITH", "EXPLAIN"}:
        raise UnsafeQueryError(
            f"Statement type '{statement_type}' is not permitted. "
            "OpsIntel only allows SELECT, WITH, and EXPLAIN."
        )

    # Remove SQL comments before checking dangerous keywords.
    without_comments = re.sub(
        r"--[^\n]*|/\*.*?\*/",
        " ",
        normalized,
        flags=re.DOTALL,
    )

    # Check complete SQL tokens rather than substrings.
    tokens = set(
        re.findall(
            r"\b[A-Za-z_][A-Za-z0-9_]*\b",
            without_comments.upper(),
        )
    )

    dangerous = tokens.intersection(FORBIDDEN_KEYWORDS)

    if dangerous:
        found = ", ".join(sorted(dangerous))
        raise UnsafeQueryError(
            f"Unsafe SQL detected: {found}. "
            "OpsIntel is strictly read-only."
        )

    return normalized
