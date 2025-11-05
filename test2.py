from langchain_classic.memory.buffer_window import ConversationBufferWindowMemory
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# loader = PyPDFLoader("Data/3body.pdf")
loader = TextLoader("Data/maxV.txt", encoding="UTF-8")
documents = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100, separators=["\n", "."])
new_chunks = splitter.split_documents(documents)

print(new_chunks[0])
