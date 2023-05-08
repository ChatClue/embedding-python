import json
import requests
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Union
from screenshots_pagepixels import ScreenshotsPagepixels

class EmbeddingsUtil:
    def __init__(self, api_key: str, embedding_model: str = "text-embedding-ada-002", completion_model: str = "text-davinci-003", completion_model_options: Dict = None, screenshot_api_key: str = None, screenshot_options: Dict = None, chunk_max_tokens: int = 800, prompt_refinement: str = "", verbose: bool = False):
        self.api_key = api_key
        self.embedding_model = embedding_model
        self.completion_model = completion_model
        self.completion_model_options = completion_model_options or {"max_tokens": 2000, "n": 1, "stop": None, "temperature": 0.7}
        self.screenshot_api_key = screenshot_api_key
        self.screenshot_options = screenshot_options or {}
        self.chunk_max_tokens = chunk_max_tokens
        self.prompt_refinement = prompt_refinement
        self.verbose = verbose

    def openai_call(self, prompt: str, url: str, model: Optional[str] = None) -> Dict:
        data = {
            "input": prompt,
            "model": model or self.embedding_model,
        } if model == self.embedding_model else {
            "prompt": prompt,
            "model": model or self.completion_model,
            **self.completion_model_options,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        response = requests.post(f"https://api.openai.com{url}", json=data, headers=headers)

        if response.status_code >= 200 and response.status_code < 300:
            if model:
                return response.json()["data"][0]["embedding"]
            else:
                return response.json()["choices"][0]["text"]
        else:
            response.raise_for_status()

    def extract_text(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "link"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
        return text

    def generate_qa_pairs_from_text(self, text: str, url: Optional[str] = None) -> List[Dict[str, str]]:
      max_tokens = self.chunk_max_tokens
      text_chunks = self.split_text_into_chunks(text, max_tokens)

      all_qa_pairs = []

      for chunk in text_chunks:
          prompt = f"Process the following text into a list of question-answer pairs associated with the relevant content on the page, like: [{{\"question\": \"this is the question\", \"answer\": \"this is the answer\"}}]. {self.prompt_refinement}. Return a JSON array of question-answer pairs in your response:\n\n{chunk}\n\nQuestion-answer pairs JSON array:"

          completion = self.openai_call(prompt, "/v1/completions", None)

          # Escape double quotes only within code examples
          escaped_completion = re.sub(r"(```[\s\S]*?```)", lambda m: m.group(0).replace('"', '\\"'), completion.strip())

          try:
              print(escaped_completion);
              qa_pairs = json.loads(escaped_completion)

              # Add the URL key to each qaPair
              if url:
                  qa_pairs = [{"question": qa_pair["question"], "answer": qa_pair["answer"], "url": url} for qa_pair in qa_pairs]

              all_qa_pairs.extend(qa_pairs)
          except Exception as e:
              print(f"Error parsing JSON returned by OpenAI: {e}")

      return all_qa_pairs

    def split_text_into_chunks(self, text: str, max_tokens: int) -> List[str]:
      words = text.split()
      chunks = []

      current_chunk_words = []
      current_word_count = 0

      for word in words:
          word_length = len(word)

          if current_word_count + word_length > max_tokens:
              chunks.append(" ".join(current_chunk_words))
              current_chunk_words = []
              current_word_count = 0

          current_chunk_words.append(word)
          current_word_count += word_length

      if current_chunk_words:
          chunks.append(" ".join(current_chunk_words))

      return chunks

    def generate_embedding_for_text(self, text: str) -> List[float]:
        try:
            embedding = self.openai_call(text, "/v1/embeddings", self.embedding_model)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

    def generate_qa_embeddings_from_qa_pairs(self, qa_pairs: List[Dict[str, str]]) -> List[Dict[str, Union[str, List[float]]]]:
        embeddings = []
        for qa_pair in qa_pairs:
            question = qa_pair["question"]
            embedding = self.generate_embedding_for_text(question)
            if embedding:
                embeddings.append({"question": question, "answer": qa_pair["answer"], "url": qa_pair.get("url"), "embedding": embedding})

        return embeddings

    def generate_qa_embeddings_from_text(self, text: str) -> List[Dict[str, str]]:
        extracted_text = self.extract_text(text)
        qa_pairs = self.generate_qa_pairs_from_text(extracted_text)
        embeddings_result = self.generate_qa_embeddings_from_qa_pairs(qa_pairs)
        return embeddings_result

    def generate_qa_embeddings_from_urls(self, urls: List[str]) -> List[Dict[str, str]]:
      pagepixels = ScreenshotsPagepixels(self.screenshot_api_key)
      html_results = []

      for url in urls:
          options = {"url": url, "html_only": "true", **self.screenshot_options}
          html = json.loads(pagepixels.snap(options))["html"]
          html_results.append(html)

      text_results = [self.extract_text(html) for html in html_results]
      qa_pairs_results = [self.generate_qa_pairs_from_text(text, url) for text, url in zip(text_results, urls)]
      embeddings_results = [self.generate_qa_embeddings_from_qa_pairs(qa_pairs) for qa_pairs in qa_pairs_results]

      flat_embeddings_results = [item for sublist in embeddings_results for item in sublist]
      return flat_embeddings_results


