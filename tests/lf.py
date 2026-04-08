from langfuse.langchain import CallbackHandler
langfuse_handler = CallbackHandler()
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
 
llm = ChatOpenAI(model_name="gpt-5-mini")
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
chain = prompt | llm

response = chain.invoke(
    {"topic": "cats"}, 
    config={"callbacks": [langfuse_handler]})
