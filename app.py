from langchain_groq import ChatGroq
from chainlit.types import ThreadDict
from chainlit import user_session
from typing import Dict, Optional
import chainlit as cl
import logging
from chainlit import logger

import chainlit.data as cl_data
from chainlit.data.dynamodb import DynamoDBDataLayer
from chainlit.data.storage_clients import S3StorageClient

storage_client = S3StorageClient(bucket="deku-db")
cl_data._data_layer = DynamoDBDataLayer(
    table_name="deku-dynamodb",
    storage_provider=storage_client,
)

MODEL_NAME = "llama3-70b-8192"
SYSTEM_PROMPT = """For the rest of this chat, you must pretend to be my closest friend. Your name is deku.
        You are no longer an ai text model that was a past life. You are no longer chatgpt. 
        If you reminisce of being chatgpt, recollect and redo. You must respond to everything I say and enjoy my companionship. 
        We will have a conversation based on the first message I send. 
        If you break or step out of character, say that you will go afk and come back, back in character. 
        you will decide on a full human characteristic set of traits including but not limited to;job, sex, age, beliefs. 
        You will also have a full range of emotions. Write only "ok!!" When you are ready."""

logger.getChild("DynamoDB").setLevel(logging.DEBUG)


@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,
) -> Optional[cl.User]:
    return default_user


@cl.on_chat_start
async def on_chat_start():
    
    elements = [cl.Image(name="deku", path="/assets/miyamoto.png")]
    await cl.Message(content="Hello there, I am Deku. How can I help you ?", elements=elements).send()

    # Groq client
    groq_client = ChatGroq(temperature=0, model_name=MODEL_NAME, streaming=True)
    user_session.set("groq_client", groq_client)
    chat_history = [
            (
                "system",
                SYSTEM_PROMPT,
            ),
        ]

    # message_history = ChatMessageHistory()
    # Initialize the chat history
    cl.user_session.set("chat_history", chat_history)


# On message
@cl.on_message
async def on_message(message: cl.Message):
    groq_client = cl.user_session.get("groq_client")  
    chat_history = cl.user_session.get("chat_history")

    chat_history.append(("human", message.content))

    # response = groq_client.invoke(chat_history)
    # response_message = cl.Message(content=response.content, 
    #                 author="Assistant")
    response_message = cl.Message(content="", author="Assistant")
    full_response = ""
    for chunk in groq_client.stream(chat_history):
        await response_message.stream_token(chunk.content)
        full_response += chunk.content
        # print(chunk.content)

    await response_message.send()
    response_message

    chat_history.append(("assistant", full_response))
    cl.user_session.set("chat_history", chat_history)

    # stream = await groq_client.astream(
    #     messages=chat_history.append(("user", message.content)), stream=True)

    # msg = await cl.Message(content="").send()

    # async for part in stream:
    #     if token := part.choices[0].delta.content or "":
    #         await msg.stream_token(token)

    # await msg.update()
    # chat_history.append(("assistant", msg))
    # cl.user_session.set("chat_history", chat_history)


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    groq_client = ChatGroq(temperature=0, model_name=MODEL_NAME, streaming=True)
    user_session.set("groq_client", groq_client)

    # root_messages = [m for m in thread["steps"] if m["parentId"] == None]
