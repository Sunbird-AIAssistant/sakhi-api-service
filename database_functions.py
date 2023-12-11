import asyncpg
import os
from datetime import datetime
import pytz


async def create_engine(timeout=60):
    engine = await asyncpg.create_pool(
        host=os.getenv('DATABASE_IP'),
        port=os.getenv('DATABASE_PORT'),
        user=os.getenv('DATABASE_USERNAME'),
        password=os.getenv('DATABASE_PASSWORD'),
        database=os.getenv('DATABASE_NAME'), max_inactive_connection_lifetime=timeout,
        max_size=20,
        min_size=10
    )
    await create_schema(engine)
    return engine


async def create_schema(engine):
    async with engine.acquire() as connection:
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS qa_voice_logs (
                id SERIAL PRIMARY KEY,
                uuid_number TEXT,
                input_language TEXT DEFAULT 'en',
                output_format TEXT DEFAULT 'TEXT',
                query TEXT,
                query_in_english TEXT,
                paraphrased_query TEXT,
                response TEXT,
                response_in_english TEXT,
                audio_output_link TEXT,
                source_text TEXT,
                error_message TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS sb_qa_logs (
                id SERIAL PRIMARY KEY,
                model_name TEXT DEFAULT 'gtp3',
                uuid_number TEXT,
                question_id TEXT,
                query TEXT,
                paraphrased_query TEXT,
                response TEXT,
                source_text TEXT,
                error_message TEXT,
                upvotes INTEGER DEFAULT 0,
                downvotes INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        ''')

async def insert_qa_voice_logs(engine, uuid_number, input_language, output_format, query, query_in_english,
                               paraphrased_query, response, response_in_english, audio_output_link, source_text,
                               error_message):
    async with engine.acquire() as connection:
        await connection.execute(
            '''
            INSERT INTO qa_voice_logs 
            (uuid_number, input_language, output_format, query, query_in_english, paraphrased_query, response, 
            response_in_english, audio_output_link, source_text, error_message, created_at) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ''',
            uuid_number, input_language, output_format, query, query_in_english, paraphrased_query, response,
            response_in_english, audio_output_link, source_text, error_message, datetime.now(pytz.UTC)
        )

async def insert_sb_qa_logs(engine, model_name, uuid_number, question_id, query, paraphrased_query, response, source_text,
                         error_message):
    async with engine.acquire() as connection:
        await connection.execute(
            '''
            INSERT INTO sb_qa_logs 
            (model_name, uuid_number,question_id, query, paraphrased_query, response, source_text, error_message, created_at) 
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ''',
            model_name, uuid_number, question_id, query, paraphrased_query, response, source_text, error_message, datetime.now(pytz.UTC)
        )