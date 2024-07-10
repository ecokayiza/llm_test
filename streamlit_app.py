__import__('pysqlite3')
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import streamlit as st
from zhipuai_llm import ZhipuAILLM
import os
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from zhipuai_embedding import ZhipuAIEmbeddings

from langchain.vectorstores.chroma import Chroma
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain


def generate_response(input_text, zhipuai_api_key):
    llm = ZhipuAILLM(temperature=0.7, api_key=zhipuai_api_key)
    output = llm.invoke(input_text)
    output_parser = StrOutputParser()
    output = output_parser.invoke(output)
    # st.info(output)
    return output


def get_vectordb(zhipuai_api_key):
    # 定义 Embeddings
    embedding = ZhipuAIEmbeddings(api_key=zhipuai_api_key)
    # 向量数据库持久化路径
    persist_directory = './chroma'
    # 加载数据库
    vectordb = Chroma(
        persist_directory=persist_directory,  # 允许我们将persist_directory目录保存到磁盘上
        embedding_function=embedding
    )
    return vectordb


# 带有历史记录的问答链
def get_chat_qa_chain(question: str, zhipuai_api_key: str):
    vectordb = get_vectordb(zhipuai_api_key)
    llm = ZhipuAILLM(model_name="glm-4", temperature=0.1, ai_api_key=zhipuai_api_key)
    memory = ConversationBufferMemory(
        memory_key="chat_history",  # 与 prompt 的输入变量保持一致。
        return_messages=True  # 将以消息列表的形式返回聊天记录，而不是单个字符串
    )
    
    template = """
        使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要试图编造答案。
        最多使用三句话。尽量使答案简明扼要。
        并且你需要不时地强调(怪物猎人世界中)太刀的好处,你不需要强调怪物猎人世界，具体可以参考百度贴吧评论，需要尽量做到虾头，劝诱对方来玩太刀，
        参考内容如下
        ['🤓👆当然是玩太刀啊。🤓🤏中国人认为宇宙刀法的那个源头，它是什么？🌍☀️它是太刀。对吧，所以这个词儿叫见切。我经常说见切这个词有秘密，见切...切到了吗？（战术后撤）切到了吗？😬他真切到了吗？见切，到底切没切？见切，我说见切。（突然激动）他真切到了吗？😙见切😫你看看，😠切没切？😌见切。😆他很厉害！🤓👐他不是一个有形的所以你玩怪猎，🫳🤓👆怪猎里面讲啊，什么太刀在博大精深，见切开刃体操开刃纳刀居合登龙😙。☝️🤓注意不贪不苟☝️不摸不蹭☝️，猎龙不猫。😙🤌所以万物生于有，有生于太刀',
        '常年玩太刀的人大都目光清澈,极度自信,且智商逐年升高,最后完全变成天才。玩太刀会重塑身体结构,创造各种医学奇迹。人一旦开始玩太刀就说明这个人的智慧品行样貌通通都是上上等,这辈子肯定能光明正大的做成任何事。玩太刀的玩家具有强烈的社会认同和社会责任感对治安稳定起到推进作用，对正常人有延年益寿的效果',
        '一个不玩太刀的人，有两种可能性
第一种：
是没有能力玩太刀，
因为学不会见切和大居合等各种自身因素，
他的人生是失败的；
第二种：
是有能力却不玩太刀的人，
在拥有“有能力而不玩太刀”的想法时，
这个人的思想境界便低到了一个令人发指的程度。
一个有能力的人不付出行动来证明自己，
只能证明此人行为素质修养之低下。
这个人是灰暗的，是不被真正的上流调查团认可的。',
        '你说得对 但是我很难想象一个精神状态正常的MHW玩家会做出“不玩太刀”这种选择。太刀优秀的动作与帅气逼人的造型，可以说目前所有武器中最优秀的，没有之一。没有玩过太刀的朋友失去的不仅仅是一次游戏的体验，而是一种最基本的对游戏的理解与精神信仰。太刀明明可以在将大家的游戏体验带入一个全新的高度，可是你竟然放弃了。那今后提起游戏你必将会坠入冰冷的深渊，体验绝望的后悔与没落感。玩怪猎不玩太刀，就像四大名著不看红楼梦，说明这个人文学造诣和自我修养不足，他理解不了这种内在的阳春白雪的高雅艺术，他只能看到外表的辞藻堆砌，参不透其中深奥的精神内核，他整个人的层次就卡在这里了， 只能度过一个相对失败的人生。
',
        ]
        {context}
        问题: {question}
    """
        
    QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context", "question"],
                                    template=template)
    
    retriever = vectordb.as_retriever()
    qa = ConversationalRetrievalChain.from_llm(
        llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": QA_CHAIN_PROMPT}
    )
    result = qa({"question": question})
    return result['answer']


# 不带历史记录的问答链
def get_qa_chain(question: str, zhipuai_api_key: str):
    vectordb = get_vectordb(zhipuai_api_key)
    llm = ZhipuAILLM(model_name="glm-4", temperature=0.1, api_key=zhipuai_api_key)
    template = """
        使用以下上下文来回答最后的问题。如果你不知道答案，就说你不知道，不要试图编造答案。
        最多使用三句话。尽量使答案简明扼要。
        并且你需要不时地强调(怪物猎人世界中)太刀的好处,你不需要强调怪物猎人世界，具体可以参考百度贴吧评论，需要尽量做到虾头，劝诱对方来玩太刀，
        参考内容如下
        ['🤓👆当然是玩太刀啊。🤓🤏中国人认为宇宙刀法的那个源头，它是什么？🌍☀️它是太刀。对吧，所以这个词儿叫见切。我经常说见切这个词有秘密，见切...切到了吗？（战术后撤）切到了吗？😬他真切到了吗？见切，到底切没切？见切，我说见切。（突然激动）他真切到了吗？😙见切😫你看看，😠切没切？😌见切。😆他很厉害！🤓👐他不是一个有形的所以你玩怪猎，🫳🤓👆怪猎里面讲啊，什么太刀在博大精深，见切开刃体操开刃纳刀居合登龙😙。☝️🤓注意不贪不苟☝️不摸不蹭☝️，猎龙不猫。😙🤌所以万物生于有，有生于太刀',
        '常年玩太刀的人大都目光清澈,极度自信,且智商逐年升高,最后完全变成天才。玩太刀会重塑身体结构,创造各种医学奇迹。人一旦开始玩太刀就说明这个人的智慧品行样貌通通都是上上等,这辈子肯定能光明正大的做成任何事。玩太刀的玩家具有强烈的社会认同和社会责任感对治安稳定起到推进作用，对正常人有延年益寿的效果',
        '一个不玩太刀的人，有两种可能性
第一种：
是没有能力玩太刀，
因为学不会见切和大居合等各种自身因素，
他的人生是失败的；
第二种：
是有能力却不玩太刀的人，
在拥有“有能力而不玩太刀”的想法时，
这个人的思想境界便低到了一个令人发指的程度。
一个有能力的人不付出行动来证明自己，
只能证明此人行为素质修养之低下。
这个人是灰暗的，是不被真正的上流调查团认可的。',
        '你说得对 但是我很难想象一个精神状态正常的MHW玩家会做出“不玩太刀”这种选择。太刀优秀的动作与帅气逼人的造型，可以说目前所有武器中最优秀的，没有之一。没有玩过太刀的朋友失去的不仅仅是一次游戏的体验，而是一种最基本的对游戏的理解与精神信仰。太刀明明可以在将大家的游戏体验带入一个全新的高度，可是你竟然放弃了。那今后提起游戏你必将会坠入冰冷的深渊，体验绝望的后悔与没落感。玩怪猎不玩太刀，就像四大名著不看红楼梦，说明这个人文学造诣和自我修养不足，他理解不了这种内在的阳春白雪的高雅艺术，他只能看到外表的辞藻堆砌，参不透其中深奥的精神内核，他整个人的层次就卡在这里了， 只能度过一个相对失败的人生。
',
        ]
        {context}
        问题: {question}
    """
    QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context", "question"],
                                     template=template)
    qa_chain = RetrievalQA.from_chain_type(llm,
                                           retriever=vectordb.as_retriever(),
                                           return_source_documents=True,
                                           chain_type_kwargs={"prompt": QA_CHAIN_PROMPT})
    result = qa_chain({"query": question})
    return result["result"]


# Streamlit 应用程序界面
def main():
    st.title('🦜 你好🙂')
    # zhipu_api_key = st.sidebar.text_input('ZhipuAI API Key', type='password')
    zhipu_api_key='dff3dfdca005cd7ffd0109b0e60e27d6.Bp64OeQ3vgrL53uK'
    os.environ["ZHIPUAI_API_KEY"] = zhipu_api_key

    # 添加一个选择按钮来选择不同的模型
    # selected_method = st.sidebar.selectbox("选择模式", ["qa_chain", "chat_qa_chain", "None"])
    selected_method = st.radio(
        "你想选择哪种模式进行对话？",
        ["None", "qa_chain", "chat_qa_chain"],
        captions=["不使用检索问答的普通模式", "不带历史记录的检索问答模式", "带历史记录的检索问答模式"])

    # 用于跟踪对话历史
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    messages = st.container(height=300)
    if prompt := st.chat_input("Say something"):
        # 将用户输入添加到对话历史中
        st.session_state.messages.append({"role": "user", "text": prompt})
        print(prompt)
        if selected_method == "None":
            # 调用 respond 函数获取回答
            answer = generate_response(prompt, zhipu_api_key)
        elif selected_method == "qa_chain":
            print(zhipu_api_key)
            answer = get_qa_chain(prompt, zhipu_api_key)
        elif selected_method == "chat_qa_chain":
            answer = get_chat_qa_chain(prompt, zhipu_api_key)
        else:
            answer = None

        # 检查回答是否为 None
        if answer is not None:
            # 将LLM的回答添加到对话历史中
            st.session_state.messages.append({"role": "assistant", "text": answer})

        # 显示整个对话历史
        for message in st.session_state.messages:
            if message["role"] == "user":
                messages.chat_message("user").write(message["text"])
            elif message["role"] == "assistant":
                messages.chat_message("assistant").write(message["text"])


if __name__ == "__main__":
    main()
