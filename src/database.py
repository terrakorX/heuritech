import os
import psycopg
from typing import Dict, Optional
from dotenv import load_dotenv
import json
from loguru import logger as log

author_statement = "INSERT INTO auteur (id_auteur ,name ,date_creation ,karma_post ,karma_com ,link_profil) VALUES"
post_statement = "INSERT INTO post (id_auteur, id_post,titre ,text,date_creation,upvotes,comments,type_piece_jointe, piece_jointe) VALUES"


def connection():
    """
    Établit une connexion à la base de données PostgreSQL après validation des variables d'environnement.
    """
    load_dotenv()

    # Récupération et validation des variables d'environnement
    try:
        user = os.getenv("POSTGRES_USER")
        if not user:
            raise ValueError(
                "POSTGRES_USER is not set or is empty in the environment variables."
            )

        password = os.getenv("POSTGRES_PASSWORD")
        if not password:
            raise ValueError(
                "POSTGRES_PASSWORD is not set or is empty in the environment variables."
            )

        dbname = os.getenv("POSTGRES_DB")
        if not dbname:
            raise ValueError(
                "POSTGRES_DB is not set or is empty in the environment variables."
            )

        host = os.getenv("POSTGRES_HOST")
        if not host:
            raise ValueError(
                "POSTGRES_HOST is not set or is empty in the environment variables."
            )

        port = os.getenv("POSTGRES_PORT")
        if not port:
            raise ValueError(
                "POSTGRES_PORT is not set or is empty in the environment variables."
            )
        # Établir la connexion
        try:
            conn = psycopg.connect(
                dbname=dbname, user=user, password=password, host=host, port=port
            )
            log.debug("Database connection successful!")
            return conn
        except Exception as error:
            raise error

    except ValueError as e:
        raise e


def bulk_insert(data: dict) -> (object, object):
    """
    Insert une liste de données dans la base de données
    """
    log.debug("preparing bulk insert")
    author_query = author_statement + ",".join(
        ["(%s,%s,%s,%s,%s,%s)" for _ in range(len(data["posts"]))]
    )
    post_query = post_statement + ",".join(
        ["(%s,%s,%s,%s,%s,%s,%s,%s,%s)" for _ in range(len(data["posts"]))]
    )
    author_args = [
        elem
        for post in data["posts"]
        for elem in (
            post["authorId"],
            post["authorProfile"].rstrip("/").split("/")[-1],
            post["cake_day"],
            post["user_karma"],
            post["comment_user_karma"],
            post["authorProfile"],
        )
    ]

    post_args = [
        elem
        for post in data["posts"]
        for elem in (
            post["authorId"],
            post["postId"],
            post["title"],
            post["text"],
            post["publishingDate"],
            post["postUpvotes"],
            post["commentCount"],
            post["attachmentType"] if post["attachmentType"] != 'text' else None ,
            post["attachmentLink"]
        )
    ]
    log.debug("bulk insert ready!")
    return (
        {"author_query": author_query, "author_args": author_args},
        {"posts_query": post_query, "posts_args": post_args},
    )


def pg_query(conn: connection, query: str, args: Optional[list] = None):
    """
    Fais une requete psql (query) avec les arguments (args)
    """
    if args is not None:
        try:
            cusor = conn.cursor()
            response = cusor.execute(query, args)
            print(response.rowcount)
            conn.commit()
            return response.rowcount
        except (Exception, psycopg.DatabaseError) as error:
            log.error(f"an error occured during insert {error}")


def insert_postgres(conn : connection, data: Dict):
    """
    Insert les auteurs ainsi que les post dans la base de donnes postgres
    """
    author, posts = bulk_insert(data)
    log.debug("inserting author data into postgres")
    inserted_auteur = pg_query(conn, f"{author["author_query"]} ON CONFLICT (id_auteur) DO NOTHING", author["author_args"])
    log.success("inserting posts data into postgres")
    inserted_post = pg_query(conn, f"{posts["posts_query"]} ON CONFLICT (id_post) DO NOTHING", posts["posts_args"])
    log.success(f"Insert coomplete of {inserted_auteur} and {inserted_post} posts")