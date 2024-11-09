"""Custom index classes for Django Pint Field."""

from collections.abc import Sequence  # pylint: disable=E0611

from django.db.models import Index
from django.db.models import Q
from django.db.models.sql import Query


class PintFieldComparatorIndex(Index):
    """Creates an index on the comparator component(s) of one or more Pint fields."""

    def __init__(
        self,
        *,
        fields: Sequence[str] = (),
        name: str = None,
        db_tablespace: str = None,
        opclasses: Sequence[str] = (),
        condition: Q = None,
        include: Sequence[str] = (),
    ) -> None:
        """Initialize the PintFieldComparatorIndex object."""
        if not isinstance(fields, (list, tuple)):
            raise ValueError("PintFieldComparatorIndex.fields must be a list or tuple.")
        if not fields:
            raise ValueError("At least one field is required for PintFieldComparatorIndex.")

        super().__init__(
            fields=fields,
            name=name,
            db_tablespace=db_tablespace,
            opclasses=opclasses,
            condition=condition,
            include=include,
        )

    def _get_condition_sql(self, model, schema_editor):
        """Convert Q object condition to SQL WHERE clause."""
        if self.condition is None:
            return ""

        # Create a dummy query to use the compiler
        query = Query(model)

        # Add the Q object to the where clause
        query.add_q(self.condition)

        # Get the SQL compiler
        compiler = query.get_compiler(connection=schema_editor.connection)

        # Get the where clause SQL and params
        where_sql, where_params = query.where.as_sql(compiler, schema_editor.connection)

        # Replace parameter placeholders with actual values
        if where_params:
            for param in where_params:
                if hasattr(param, "magnitude"):
                    # For Pint Quantities, use the base units magnitude
                    param_value = param.to_base_units().magnitude
                else:
                    param_value = param
                where_sql = where_sql.replace("%s", str(param_value), 1)

        return f" WHERE {where_sql}"

    def create_sql(self, model, schema_editor, using="", **kwargs) -> str:
        """Generate SQL for creating the index with correct composite type field access."""
        quote_name = schema_editor.quote_name
        table_name = model._meta.db_table  # pylint: disable=W0212

        # Generate index name if not provided
        if not self.name:
            field_names = "_".join(self.fields)
            self.name = f"{table_name}_{field_names}_comparator_idx"

        # Build index expressions for composite type fields
        index_expressions = []
        for field in self.fields:
            # For composite types in Postgres, use (field).comparator expression
            index_expressions.append(f"(({quote_name(field)}).comparator)")

        # Join the expressions with commas for multi-field indexes
        index_columns = ", ".join(index_expressions)

        # Add INCLUDE clause if specified
        include_clause = ""
        if self.include:
            include_columns = ", ".join(quote_name(field) for field in self.include)
            include_clause = f" INCLUDE ({include_columns})"

        # Add tablespace clause if specified
        tablespace_clause = ""
        if self.db_tablespace:
            tablespace_clause = f" TABLESPACE {quote_name(self.db_tablespace)}"

        # Add condition clause if specified
        condition_clause = self._get_condition_sql(model, schema_editor)

        # Create the complete SQL statement
        sql = (
            f"CREATE INDEX {quote_name(self.name)} ON {quote_name(table_name)} "
            f"({index_columns}){include_clause}{condition_clause}{tablespace_clause}"
        )

        return sql

    def remove_sql(self, model, schema_editor, using="", **kwargs) -> str:  # pylint: disable=W0613
        """Generate SQL for removing the index."""
        quote_name = schema_editor.quote_name
        return f"DROP INDEX IF EXISTS {quote_name(self.name)}"

    def deconstruct(self):
        """Return a 3-tuple of class import path, args, and kwargs."""
        path = f"{self.__class__.__module__}.{self.__class__.__name__}"
        args = ()
        kwargs = {
            "fields": self.fields,
            "name": self.name,
            "db_tablespace": self.db_tablespace,
            "opclasses": self.opclasses,
            "condition": self.condition,
            "include": self.include,
        }
        return path, args, kwargs
