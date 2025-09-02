from langchain_community.document_loaders import DirectoryLoader
from langchain_unstructured import UnstructuredLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document
import os

class KnowledgeBase:
    def __init__(self, persist_directory="knowledge_base"):
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(model_name="shibing624/text2vec-base-chinese")
        
        # 如果向量库已存在，直接加载
        if os.path.exists(persist_directory):
            self.db = Chroma(persist_directory=persist_directory, 
                           embedding_function=self.embeddings)
        else:
            self.db = None

    def add_documents(self, directory_path):
        """添加文档到知识库"""
        # 加载文档
        loader = DirectoryLoader(directory_path, 
                               glob="**/*.*",
                               show_progress=True)
        documents = loader.load()
        
        # 分割文档
        text_splitter = CharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separator="\n"
        )
        texts = text_splitter.split_documents(documents)
        
        # 创建或更新向量库
        if self.db is None:
            self.db = Chroma.from_documents(texts, 
                                          self.embeddings, 
                                          persist_directory=self.persist_directory)
        else:
            self.db.add_documents(texts)
        
        self.db.persist()
        return len(texts)

    def search(self, query, k=3):
        """搜索相关文档"""
        if self.db is None:
            return []
        
        docs = self.db.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

    def add_single_file(self, file_path):
        """添加单个文件到知识库"""
        loader = UnstructuredLoader(file_path)
        raw_documents = loader.load()
        
        # 确保文档格式正确
        documents = []
        for doc in raw_documents:
            if isinstance(doc, str):
                # 如果是字符串，创建Document对象
                documents.append(Document(
                    page_content=doc,
                    metadata={"source": file_path}
                ))
            else:
                # 如果已经是Document对象，直接使用
                documents.append(doc)
        
        # 分割文档
        text_splitter = CharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separator="\n"
        )
        texts = text_splitter.split_documents(documents)
        
        if self.db is None:
            self.db = Chroma.from_documents(texts, 
                                          self.embeddings, 
                                          persist_directory=self.persist_directory)
        else:
            self.db.add_documents(texts)
        
        self.db.persist()
        return len(texts) 