from sentence_transformers import SentenceTransformer, util
import os
import pickle
import pandas as pd
from functools import lru_cache
from scraping import scrape_doctors

file_path = r"C:\Users\kunda\Downloads\train.csv"
questions, answers, question_embeddings = None, None, None

# Function to load data and compute embeddings

# Path to cache the embeddings and related data
cache_file_path = "embedding_cache.pkl"

def chatbot(input):

    user_input = input

    @lru_cache(maxsize=None)
    def load_data_and_compute_embeddings(file_path):
        # Initialize the Sentence-BERT model (needed regardless of cache)
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # Try loading the cached embeddings
        if os.path.exists(cache_file_path):
            try:
                with open(cache_file_path, 'rb') as f:
                    cached_data = pickle.load(f)
                    questions = cached_data['questions']
                    answers = cached_data['answers']
                    question_embeddings = cached_data['question_embeddings']
                    print("Loaded cached embeddings.")
                    return questions, model, answers, question_embeddings
            except (EOFError, pickle.UnpicklingError):
                print("Cache file is corrupted or incomplete. Recomputing embeddings...")
                os.remove(cache_file_path)  # Remove the corrupted cache file
        
        # Load the dataset if no valid cache is found
        print("Cache not found. Computing embeddings...")
        data = pd.read_csv(file_path)
        questions = data['Question'].values
        answers = data['Answer'].values
        
        # Precompute question embeddings
        question_embeddings = model.encode(questions, convert_to_tensor=True, show_progress_bar=True)
        
        # Cache the embeddings and data
        with open(cache_file_path, 'wb') as f:
            pickle.dump({
                'questions': questions,
                'answers': answers,
                'question_embeddings': question_embeddings
            }, f)
        
        print("Embeddings computed and cached.")
        return questions, model, answers, question_embeddings

    # Load dataset and compute embeddings
    questions,model, answers, question_embeddings = load_data_and_compute_embeddings(file_path)

    # Define a dictionary of generic responses for greetings and other conversational inputs
    generic_responses = {
        "hi": "Hello! How can I assist you today?",
        "hello": "Hi there! How can I help you?",
        "hey": "Hey! How can I assist?",
        "how are you": "I'm a chatbot, but I'm here to help you with any medical questions!",
        "good morning": "Good morning! How can I assist you today?",
        "good afternoon": "Good afternoon! What can I do for you today?",
        "good evening": "Good evening! How can I assist you?",
        "thanks": "You're welcome! Feel free to ask more questions.",
        "thank you": "You're welcome! How else can I assist you?",
    }

    # Function to handle generic inputs with predefined responses
    def get_generic_response(user_input):
        user_input_lower = user_input.lower()
        for greeting, response in generic_responses.items():
            if greeting in user_input_lower:
                return response
        return None

    # Function to find the best match for a given question
    def get_best_match(user_question, model, question_embeddings, questions, answers, top_n=5):
        # Encode the user question
        user_question_embedding = model.encode(user_question, convert_to_tensor=True)
        similarity_scores = util.pytorch_cos_sim(user_question_embedding, question_embeddings).flatten()
        top_n_indices = similarity_scores.topk(k=top_n).indices.cpu().numpy()
        best_question = questions[top_n_indices[0]]  # Get the best match
        best_answer = answers[top_n_indices[0]]
        
        if similarity_scores[top_n_indices[0]] < 0.5:
            return "I am sorry, can you describe your question more precisely?"
        
        return best_answer
    
    generic_responses = get_generic_response(user_input)
    if generic_responses:
        output = generic_responses
    else:
        output = get_best_match(user_input, model, question_embeddings, questions, answers, top_n=5)
        
    return output
