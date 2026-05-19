from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Literal
import os
from uuid import uuid4
from openai import AsyncOpenAI
import aiosqlite
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
app = FastAPI()
AUTH_TOKEN = os.getenv('AUTH_TOKEN', "dev-secret")

async def check_user(api_token: str | None = Header(None, alias="Api-token"),
                      user_id: str | None = Header(None, alias="User-id")):
    if api_token is None:
        raise HTTPException(status_code=401, detail="Missing Api-Token")
    if api_token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Incorrect Api-Token")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Missing User-Id")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM users WHERE id=? OR name=?", (user_id, user_id))
        row = await cursor.fetchone()
        if row is None:
            await db.execute("INSERT OR IGNORE INTO users VALUES(?, ?)", (user_id, user_id))
            await db.commit()
            return user_id
    return row[0]

def multiply_by_2(a: float):
        return a * 2
def devide(a: float, b: float):
    return a / b
DB_PATH = "database.db" 
BUILT_IN_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "multiply_by_2",
            "description": "Умножает число данное на входе на два",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "Входное число"
                    },
                },
                "required": ["a"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "devide",
            "description": "Делит певрое число на второе",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "Первое число"
                    },
                    "b": {
                        "type": "number",
                        "description": "Второе число"
                    },
                },
                "required": ["a", "b"]
            }
        }
    }
]
async def create_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS llm_configs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                base_url TEXT NOT NULL,
                api_key TEXT NOT NULL,
                model TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mcp_configs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                url TEXT NOT NULL,
                token TEXT NOT NULL,
                name TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                llm_config_id TEXT NOT NULL,
                built_in_arithmetic INTEGER NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_mcp_configs (
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                mcp_config_id TEXT NOT NULL,
                PRIMARY KEY (chat_id, mcp_config_id)
            )
        """)
        await db.commit()


class Message(BaseModel):
    role: str
    content: str

class Message_user(BaseModel):
    role: Literal["user"]
    content: str

class LLM_config(BaseModel):
    base_url: str
    api_key: str
    model: str

class MCP_config(BaseModel):
    url: str
    token: str
    name: str

class Chat(BaseModel):
    llm_config_id: str
    messages: list[Message]
    built_in_arithmetic: bool
    mcp_config_ids: list[str]

@app.on_event("startup")
async def startup():
    await create_db()

@app.get("/chats", status_code=200)
async def get_user_chats(user_id = Depends(check_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM chats WHERE user_id=?", (user_id,))
        rows = await cursor.fetchall()
    return [{"chat_id": row[0]} for row in rows]

@app.post("/reg/{name}", status_code=201)
async def create_user(name: str):
    if not name.strip():
        raise HTTPException(status_code=422, detail="Invalid name")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM users WHERE name=?", (name,))
        row = await cursor.fetchone()
        if row is not None:
            return {"user_id": row[0]}
        user_id = str(uuid4())
        await db.execute("INSERT INTO users VALUES(?, ?)", (user_id, name))
        await db.commit()
    return {"user_id": user_id}

@app.post('/chats/{config_id}', status_code=201)
async def create_chat(config_id: str, user_id = Depends(check_user)):
    chat_id = str(uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM llm_configs WHERE id=? AND user_id=?",
                                  (config_id, user_id))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Incorrect llm config id")
        await db.execute("INSERT INTO chats VALUES(?, ?, ?, ?)",
                         (chat_id, user_id, config_id, 1))
        await db.commit()
    return {"chat_id": chat_id}

@app.get('/chats/{chat_id}', status_code=200)
async def get_chat(chat_id: str, user_id = Depends(check_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT llm_config_id, built_in_arithmetic "
        "FROM chats WHERE id=? AND user_id=?",
        (chat_id, user_id))
        row = await cursor.fetchone()
        cursor = await db.execute("SELECT role, content "
        "FROM messages WHERE user_id=? AND chat_id=?",
        (user_id, chat_id))
        messages = await cursor.fetchall()
        cursor = await db.execute("SELECT mcp_config_id "
        "FROM chat_mcp_configs WHERE chat_id=? AND user_id=?",
        (chat_id, user_id))
        mcp_configs = await cursor.fetchall()
    if row is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"llm_config_id": row[0],
            "messages": [{"role": m[0], "content": m[1]} for m in messages],
            'mcp_config_ids': [m[0] for m in mcp_configs],
            "built_in_arithmetic": bool(row[1])}

async def add_message(chat_id: str, role: str, content: str, user_id: str):
    message_id = str(uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO messages VALUES(?, ?, ?, ?, ?)",
                         (message_id, user_id, chat_id, role, content))
        await db.commit()
    return message_id

def mcp_tool_to_openai_tool(tool):
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema,
        }
    }

async def call_mcp_tool(mcp_config, tool_name=None, arguments=None):
    async with streamablehttp_client(
        mcp_config.url,
        headers={"Authorization": f"Bearer {mcp_config.token}"}
    ) as streams:
        read_stream, write_stream, _ = streams
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            if tool_name is None:
                return await session.list_tools()
            return await session.call_tool(tool_name, arguments)

async def get_mcp_tools(mcp_configs: list[MCP_config]):
    tools = []
    for i, mcp_config in enumerate(mcp_configs, start=1):
        try:
            mcp_tools = await call_mcp_tool(mcp_config)
        except Exception:
            continue
        for tool in mcp_tools.tools:
            openai_tool = mcp_tool_to_openai_tool(tool)
            openai_tool["function"]["name"] = f"{i}_{tool.name}"
            tools.append(openai_tool)
    return tools

async def ask_llm(llm_config: LLM_config, chat: Chat, mcp_configs: list[MCP_config]):
    client = AsyncOpenAI(
        api_key=llm_config.api_key,
        base_url=llm_config.base_url
    )
    cnt_completions = 0
    message: list[dict] = [{"role": msg.role, "content": msg.content} for msg in chat.messages]
    tools = list(BUILT_IN_TOOLS) if chat.built_in_arithmetic else []
    tools += await get_mcp_tools(mcp_configs)
    last_tool = None
    repeat = 0
    while (cnt_completions < 10):
        response = await client.chat.completions.create(
            model=llm_config.model,
            messages=message,
            tool_choice="auto",
            tools=tools if tools else None
        )
        message_ = response.choices[0].message
        cnt_completions += 1
        if message_.tool_calls:
            message.append({
                "role": "assistant",
                "content": message_.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in message_.tool_calls
                ],
            })
            for tool_call in message_.tool_calls:
                function_name = tool_call.function.name
                repeat = repeat + 1 if function_name == last_tool else 1
                last_tool = function_name
                if repeat > 2:
                    raise HTTPException(status_code=400, detail=f"Tool '{function_name}' called more than 2 times in a row")
                function_args = json.loads(tool_call.function.arguments)
                if function_name == "multiply_by_2":
                    resp = multiply_by_2(function_args['a'])
                    message.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(resp)})
                elif function_name == "devide":
                    resp = devide(function_args['a'], function_args['b'])
                    message.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(resp)})
                else:
                    mcp_index = int(function_name.split("_", 1)[0]) - 1
                    tool_name = function_name.split("_", 1)[1]
                    result = await call_mcp_tool(mcp_configs[mcp_index], tool_name, function_args)
                    resp = result.content[0].text if result.content else ""
                    message.append({"role": "tool", "tool_call_id": tool_call.id, "content": str(resp)})
        else:
            return message_
    raise HTTPException(status_code=400, detail="Agent loop exceeded 10 completions")

@app.post('/chats/{chat_id}/messages', status_code=201)
async def send_message(chat_id: str, message_base: Message_user, user_id = Depends(check_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT llm_config_id, built_in_arithmetic "
        "FROM chats WHERE id=? AND user_id=?",
        (chat_id, user_id))
        row = await cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Chat not found")
        message_id = await add_message(chat_id, message_base.role, message_base.content, user_id)
        cursor = await db.execute("SELECT role, content "
        "FROM messages WHERE user_id=? AND chat_id=?",
        (user_id, chat_id))
        messages = await cursor.fetchall()
        cursor = await db.execute("SELECT mcp_config_id "
        "FROM chat_mcp_configs WHERE chat_id=? AND user_id=?",
        (chat_id, user_id))
        mcp_configs = await cursor.fetchall()
    chat = Chat(
        llm_config_id=row[0],
        messages=[Message(role=m[0], content=m[1]) for m in messages],
        built_in_arithmetic=bool(row[1]),
        mcp_config_ids=[m[0] for m in mcp_configs],
    )
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT base_url, api_key, model "
        "FROM llm_configs WHERE id=? AND user_id=?",
        (row[0], user_id))
        config = await cursor.fetchone()
        cursor = await db.execute("SELECT url, token, name FROM mcp_configs "
        "WHERE user_id=? AND id IN (SELECT mcp_config_id FROM chat_mcp_configs WHERE chat_id=? AND user_id=?)",
        (user_id, chat_id, user_id))
        mcp_rows = await cursor.fetchall()
    if config is None:
        raise HTTPException(status_code=404, detail="LLM config not found")
    llm_config = LLM_config(base_url=config[0], api_key=config[1],
                             model=config[2])
    mcp_configs = [MCP_config(url=m[0], token=m[1], name=m[2]) for m in mcp_rows]
    try:
        response = await ask_llm(llm_config, chat, mcp_configs)
    except HTTPException:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM messages WHERE id=?", (message_id,))
            await db.commit()
        raise
    await add_message(chat_id, response.role, response.content, user_id)
    return {"status": "message added", "answer": response.content}

@app.post('/chats/{chat_id}/mcp-configs/{mcp_config_id}', status_code=201)
async def add_mcp_config(chat_id: str, mcp_config_id: str, user_id = Depends(check_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM chats WHERE id=? AND user_id=?", (chat_id, user_id))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Incorrect chat-id")
        cursor = await db.execute("SELECT id FROM mcp_configs WHERE id=? AND user_id=?", (mcp_config_id, user_id))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Incorrect mcp-id")
        cursor = await db.execute("SELECT mcp_config_id FROM chat_mcp_configs "
                                  "WHERE chat_id=? AND mcp_config_id=? AND user_id=?",
                                  (chat_id, mcp_config_id, user_id))
        if await cursor.fetchone() is None:
            await db.execute("INSERT INTO chat_mcp_configs VALUES(?, ?, ?)",
                             (chat_id, user_id, mcp_config_id))
            await db.commit()
    return {"status": "mcp config added"}

@app.delete('/chats/{chat_id}/mcp-configs/{mcp_config_id}', status_code=200)
async def delete_mcp_config(chat_id: str, mcp_config_id: str, user_id = Depends(check_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM chats WHERE id=? AND user_id=?", (chat_id, user_id))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Incorrect chat-id")
        cursor = await db.execute("SELECT id FROM mcp_configs WHERE id=? AND user_id=?", (mcp_config_id, user_id))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Incorrect mcp-id")
        cursor = await db.execute("SELECT mcp_config_id FROM chat_mcp_configs "
                                  "WHERE chat_id=? AND mcp_config_id=? AND user_id=?",
                                  (chat_id, mcp_config_id, user_id))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Incorrect mcp-id, mcp not in chat")
        await db.execute("DELETE FROM chat_mcp_configs WHERE chat_id=? AND mcp_config_id=? AND user_id=?",
                         (chat_id, mcp_config_id, user_id))
        await db.commit()
    return {"status": "mcp config deleted"}


@app.post('/chats/{chat_id}/built-in-arithmetic', status_code=201)
async def enable_arithmetic(chat_id: str, user_id = Depends(check_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM chats WHERE id=? AND user_id=?", (chat_id, user_id))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Incorrect chat-id")
        await db.execute("UPDATE chats SET built_in_arithmetic=1 WHERE id=? AND user_id=?", (chat_id, user_id))
        await db.commit()
    return {"status": "Arithmetic added"}

@app.delete('/chats/{chat_id}/built-in-arithmetic', status_code=200)
async def disable_arithmetic(chat_id: str, user_id = Depends(check_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM chats WHERE id=? AND user_id=?", (chat_id, user_id))
        if await cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Incorrect chat-id")
        await db.execute("UPDATE chats SET built_in_arithmetic=0 WHERE id=? AND user_id=?", (chat_id, user_id))
        await db.commit()
    return {"status": "Arithmetic deleted"}

@app.post('/llm-configs', status_code=201)
async def create_config(config: LLM_config, user_id = Depends(check_user)):
    config_id = str(uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO llm_configs VALUES(?, ?, ?, ?, ?)",
                         (config_id, user_id, config.base_url, config.api_key, config.model))
        await db.commit()
    return {'config_id': config_id}

@app.get('/llm-configs', status_code=200)
async def get_config(user_id = Depends(check_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, model, base_url FROM llm_configs WHERE user_id=?", (user_id,))
        rows = await cursor.fetchall()
    return [{'id': row[0], 'model': row[1], 'base_url': row[2]} for row in rows]

@app.get('/llm-configs/{config_id}', status_code=200)
async def get_config_id(config_id: str, user_id = Depends(check_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, model, base_url FROM llm_configs WHERE id=? AND user_id=?",
                                  (config_id, user_id))
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='Incorrect config_id')
    return {'id': row[0], 'model': row[1], 'base_url': row[2]}

@app.post('/mcp-configs', status_code=201)
async def create_mcp_config(config: MCP_config, user_id = Depends(check_user)):
    config_id = str(uuid4())
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO mcp_configs VALUES(?, ?, ?, ?, ?)",
                         (config_id, user_id, config.url, config.token, config.name))
        await db.commit()
    return {'config_id': config_id}

@app.get('/mcp-configs', status_code=200)
async def get_mcp_config(user_id = Depends(check_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name, url FROM mcp_configs WHERE user_id=?", (user_id,))
        rows = await cursor.fetchall()
    return [{'id': row[0], 'name': row[1], 'url': row[2]} for row in rows]

@app.get('/mcp-configs/{config_id}', status_code=200)
async def get_mcp_config_id(config_id: str, user_id = Depends(check_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id, name, url FROM mcp_configs WHERE id=? AND user_id=?",
                                  (config_id, user_id))
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail='Incorrect config_id')
    return {'id': row[0], 'name': row[1], 'url': row[2]}

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

