"""CHG resize id columns

Revision ID: 70bf8c2bf6a4
Revises: 6e59d5c2d34b
Create Date: 2022-07-23 16:38:05.464637

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "70bf8c2bf6a4"
down_revision = "6e59d5c2d34b"
branch_labels = None
depends_on = None

tables = ['anubis_config', 'user', 'course', 'ta_for_course', 'professor_for_course', 'in_course', 'assignment',
          'assignment_repo', 'assignment_test', 'assignment_question', 'assigned_student_question',
          'assigned_student_response', 'submission', 'submission_test_result', 'submission_build', 'theia_image',
          'theia_image_tag', 'theia_session', 'theia_paste', 'static_file', 'late_exception', 'lecture_notes',
          'forum_post', 'forum_category', 'forum_post_in_category', 'forum_post_viewed', 'forum_post_comment',
          'forum_post_upvote']

def migrate_id(conn, table_name: str, new_size: int = 36):
    r = conn.execute('select `column_name` from `information_schema`.`columns` '
                     'where `TABLE_SCHEMA` = %s and `TABLE_NAME` = %s and `COLUMN_NAME` = %s;',
                     ('anubis', table_name, 'id'))
    if r.fetchone() is not None:
        print(f'Resizing {table_name}.id to length={new_size}')
        op.alter_column(table_name, 'id',
                        type_=sa.VARCHAR(length=new_size, collation='utf8mb4_general_ci'),
                        nullable=False)


def do_migration(new_size: int = 36):
    conn = op.get_bind()
    def quote(identifier):
        return f"`{identifier.replace('`', '``')}`"

    with conn.begin() as trx:
        result = conn.execute(sa.text(
            """SELECT k.TABLE_NAME, k.CONSTRAINT_NAME, k.COLUMN_NAME,
                      k.REFERENCED_TABLE_NAME, k.REFERENCED_COLUMN_NAME,
                      k.ORDINAL_POSITION, r.UPDATE_RULE, r.DELETE_RULE
               FROM information_schema.KEY_COLUMN_USAGE k
               JOIN information_schema.REFERENTIAL_CONSTRAINTS r
                 ON r.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA
                AND r.CONSTRAINT_NAME = k.CONSTRAINT_NAME
                AND r.TABLE_NAME = k.TABLE_NAME
               WHERE k.TABLE_SCHEMA = DATABASE()
                 AND k.REFERENCED_TABLE_NAME IS NOT NULL
               ORDER BY k.TABLE_NAME, k.CONSTRAINT_NAME, k.ORDINAL_POSITION"""
        ))
        foreign_keys = {}
        for row in result:
            key = (row[0], row[1])
            foreign_key = foreign_keys.setdefault(key, {
                "columns": [], "referenced_table": row[3], "referenced_columns": [],
                "on_update": row[6], "on_delete": row[7],
            })
            foreign_key["columns"].append(row[2])
            foreign_key["referenced_columns"].append(row[4])

        for table_name, constraint_name in foreign_keys:
            conn.execute(sa.text(
                f"ALTER TABLE {quote(table_name)} DROP FOREIGN KEY {quote(constraint_name)}"
            ))

        for table_name in tables:
            migrate_id(conn, table_name, new_size)

        for sub_table_name in tables:
            r = conn.execute(
                'select `COLUMN_NAME`, `IS_NULLABLE` from `information_schema`.`columns` '
                'where `TABLE_SCHEMA` = %s and `TABLE_NAME` = %s and `COLUMN_NAME` LIKE \'%%\\_id\';',
                ('anubis', sub_table_name))
            rr = r.fetchall()
            for key_name, nullable in rr:
                print(f'Resizing {sub_table_name}.{key_name} to length={new_size}')
                op.alter_column(sub_table_name, key_name,
                                type_=sa.VARCHAR(length=new_size, collation='utf8mb4_general_ci'),
                                nullable=nullable == 'YES')

        for (table_name, constraint_name), foreign_key in foreign_keys.items():
            columns = ", ".join(map(quote, foreign_key["columns"]))
            referenced_columns = ", ".join(map(quote, foreign_key["referenced_columns"]))
            conn.execute(sa.text(
                f"ALTER TABLE {quote(table_name)} ADD CONSTRAINT {quote(constraint_name)} "
                f"FOREIGN KEY ({columns}) REFERENCES {quote(foreign_key['referenced_table'])} "
                f"({referenced_columns}) ON UPDATE {foreign_key['on_update']} "
                f"ON DELETE {foreign_key['on_delete']}"
            ))
        trx.commit()


def upgrade():
    do_migration(new_size=36)


def downgrade():
    pass #do_migration(new_size=128)
