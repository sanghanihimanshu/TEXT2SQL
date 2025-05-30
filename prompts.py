import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder,FewShotChatMessagePromptTemplate,PromptTemplate
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from operator import itemgetter
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
import streamlit as st
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base


from similarity_search import  generating_query 



example_prompt=ChatPromptTemplate.from_messages(
        [
            ("human", "{input}\nSQLQuery:"),
            ("ai", "{query}"),
        ]
        )

def few_shot_prompt(qsn):
    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=generating_query(qsn),
        input_variables=["input","top_k","table_info"]
    )
    return few_shot_prompt






def final_prompt(qsn):
    system_msg="You are a MySQL expert. Given an input question, create a syntactically correct MySQL query to run. Unless otherwise specificed.\n\nHere is the relevant table info: {table_info}\n\nBelow are a number of examples of questions and their corresponding SQL queries."

    final_prompt = ChatPromptTemplate.from_messages(
        [
            few_shot_prompt(qsn),
            MessagesPlaceholder(variable_name="messages"),
            ("human", system_msg+"{input}")
        ]
    )
    return final_prompt


answer_prompt=PromptTemplate.from_template(
        """Given the following user question, corresponding SQL query, and SQL result, answer the user question. 
Please note that if you find a question is not related to our table, SQL, or our database  then simply respond with: "I'm sorry. I can't answer your question."
       
Instructions: 
- Base your answer solely on the provided SQL Result. 
- Do NOT include the SQL Query in your final response. 
-If the question cannot be answered from the provided information or is unrelated, respond ONLY with: "I'm sorry. I can't answer your question."
-formulate a natural language answer to the user question using the SQL result.

        Question: {question}
        SQL Query: {query}
        SQL Result: {result}
        Answer: """
        )
