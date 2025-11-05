from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
from model import Model


class RagSearch:


    def __init__(self, id, model):
        self.chunks = []
        self.vectors = []
        self.file_names = []
        self.id = id
        self.model = model
        self.model.new_session(id)


    def __cosine_similarity__(self, v1, v2):
        return np.dot(v1, v2) # / (np.linalg.norm(v1) * np.linalg.norm(v2))


    def load_file(self, file_name):
        if file_name.endswith(".pdf"):
            loader = PyPDFLoader(file_name)
        elif file_name.endswith(".txt"):
            loader = TextLoader(file_name, encoding="UTF-8")
        else:
            return False
        documents = loader.load()
        for document in documents:
            document.page_content = document.page_content.replace("-\n", "")

        splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100, separators=["\n", "."])
        new_chunks = splitter.split_documents(documents)

        self.chunks += new_chunks
        self.vectors += [self.model.embed(chunk.page_content) for chunk in new_chunks]

        self.file_names.append(file_name)

        return True


    def find(self, text):
        target_vector = self.model.embed(text)

        cos_similarityes = []
        for i in range(len(self.vectors)):
            cos_similarityes.append(self.__cosine_similarity__(target_vector, self.vectors[i])) 

        n = 6
        best_vectors = [0 for i in range(n)]
        best_similarityes = [0 for i in range(n)]
        for i in range(len(cos_similarityes)):
            ind = best_similarityes.index(min(best_similarityes))
            if cos_similarityes[i] > best_similarityes[ind]:
                best_similarityes[ind] = cos_similarityes[i]
                best_vectors[ind] = i

        sources = ""
        for ind in best_vectors:
            sources += f"[SOURCE {ind}]\n{self.chunks[ind].page_content}\n\n\n"

        answer = self.model.invoke(self.id, text, sources)

        for ind in best_vectors:
            if "page" in self.chunks[ind].metadata.keys():
                answer = answer.replace(f"SOURCE {ind}", f"{self.chunks[ind].metadata['source']}, p. {self.chunks[ind].metadata['page_label']}")
            else:
                answer = answer.replace(f"SOURCE {ind}", f"{self.chunks[ind].metadata['source']}")

        return answer
    
    def clear(self):
        self.chunks = []
        self.vectors = []
        self.file_names = []
        self.model.clear_memory(self.id)

    def get_files(self):
        return self.file_names
            


