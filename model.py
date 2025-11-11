from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_classic.memory.buffer_window import ConversationBufferWindowMemory
from langchain_core.runnables import RunnableSequence, RunnableMap
from langchain_core.prompts import PromptTemplate
from faster_whisper import WhisperModel


class Model:

    
    def __init__(self, embedding_model_name, llm_model_name):
        self.emb_model = OllamaEmbeddings(model=embedding_model_name)
        self.llm_model = OllamaLLM(model=llm_model_name, temperature=0.3)
        self.audio_model = WhisperModel("base", device="cuda")
        self.sessions = {}
        self.prompt = PromptTemplate(
            input_variables=["chat_history", "k", "text", "sources"],
            template=(
                "Чётко и как можно ближе ответь на вопрос пользователя, используя информацию только из этих источников. В конце каждого утверждения добавь [SOURCE i], откуда ты взял информацию. " +
                "Можешь использовать в ответе сразу несколько источников. Если в источниках нет информации про заданный вопрос, напиши 'В источниках нет ответа на вопрос'.\n\n" +
                "История сообщений за последние {k} запросов:\n{chat_history}\n\n" +
                "Вопрос:\n{text}\n\n" +
                "Источники:\n{sources}"
            ),
)


    def new_session(self, id):
        memory = ConversationBufferWindowMemory(memory_key="chat_history",
                                                k=3,
                                                return_messages=True)
        memory_map = RunnableMap({"chat_history": lambda x: memory.load_memory_variables({}),
                                  "k": lambda x: memory.k,
                                  "text": lambda x: x["text"],
                                  "sources": lambda x: x["sources"],})
        chain = RunnableSequence(memory_map | self.prompt | self.llm_model)
        self.sessions[id] = chain


    def embed(self, text):
        return self.emb_model.embed_query(text)
    

    def invoke(self, id, text, sources):
        if not id in self.sessions.keys():
            self.new_session(id)
        return self.sessions[id].invoke({"text": text, "sources": sources})
    

    def clear_memory(self, id):
        self.new_session(id)

    def recognize(self, audiofilen_name):
        segments, info = self.audio_model.transcribe(audiofilen_name, beam_size=5)

        text = ""
        for segment in segments:
            text += segment.text + "\n"

        return text

    