import json
import jieba
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from bert_score import score

# Initialize jieba
jieba.initialize()

# Text Processing Functions
def preprocess_text(text):
    tokens = jieba.cut(text)
    return [token.lower() for token in tokens if token.isalnum()]

def calculate_tfidf_similarity(text1, text2):
    processed_text1 = ' '.join(preprocess_text(text1))
    processed_text2 = ' '.join(preprocess_text(text2))
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([processed_text1, processed_text2])
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

def calculate_bleu(reference, candidate):
    reference_tokens = preprocess_text(reference)
    candidate_tokens = preprocess_text(candidate)
    if not reference_tokens or not candidate_tokens:
        print("Warning: Empty tokens detected")
        return 0
    weights = (0.33, 0.33, 0.34)
    smoothing = SmoothingFunction().method1
    return sentence_bleu([reference_tokens], candidate_tokens, weights=weights, smoothing_function=smoothing)

def calculate_rouge_l(reference, candidate):
    def lcs(X, Y):
        m, n = len(X), len(Y)
        L = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            for j in range(n + 1):
                if i == 0 or j == 0:
                    L[i][j] = 0
                elif X[i-1] == Y[j-1]:
                    L[i][j] = L[i-1][j-1] + 1
                else:
                    L[i][j] = max(L[i-1][j], L[i][j-1])
        return L[m][n]

    reference_tokens = preprocess_text(reference)
    candidate_tokens = preprocess_text(candidate)
    lcs_length = lcs(reference_tokens, candidate_tokens)
    if len(reference_tokens) == 0 or len(candidate_tokens) == 0:
        return 0
    recall = lcs_length / len(reference_tokens)
    precision = lcs_length / len(candidate_tokens)
    if recall + precision == 0:
        return 0
    f1 = 2 * recall * precision / (recall + precision)
    return f1

def calculate_bertscore(reference, candidate):
    P, R, F1 = score([candidate], [reference], lang="zh")
    return F1.item()  # Return the F1 score

def evaluate_student_output(prompt, chatgpt_output, student_output):
    student_evaluation = evaluate_answer(prompt, chatgpt_output, student_output)
    return student_evaluation

def evaluate_answer(prompt, chatgpt_output, answer):
    tfidf_sim = calculate_tfidf_similarity(chatgpt_output, answer)
    bleu_score = calculate_bleu(chatgpt_output, answer)
    rouge_l_score = calculate_rouge_l(chatgpt_output, answer)
    bertscore = calculate_bertscore(chatgpt_output, answer)
    prompt_relevance_chatgpt = calculate_tfidf_similarity(prompt, chatgpt_output)
    prompt_relevance_answer = calculate_tfidf_similarity(prompt, answer)
    relevance_ratio = prompt_relevance_answer / prompt_relevance_chatgpt if prompt_relevance_chatgpt > 0 else 0

    weights = {
        'tfidf': 0.20, 'bleu': 0.1, 'rouge': 0.1, 'bertscore': 0.35, 'relevance': 0.25
    }

    score = (
        tfidf_sim * weights['tfidf'] +
        bleu_score * weights['bleu'] +
        rouge_l_score * weights['rouge'] +
        bertscore * weights['bertscore'] +
        relevance_ratio * weights['relevance']
    ) * 100

    return {
        'score': score,
        'tfidf_similarity': tfidf_sim,
        'bleu_score': bleu_score,
        'rouge_l_score': rouge_l_score,
        'bertscore': bertscore,
        'prompt_relevance_ratio': relevance_ratio
    }

# Utility function to load questions from JSON
def load_questions_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

if __name__ == "__main__":
    # Example 
    prompt = "請簡要介紹明朝的建立過程及其特點。"
    chatgpt_output = "明朝的建立是由朱元璋領導的。他出身貧農，加入紅巾軍起義後逐漸崛起。1368年，朱元璋成功推翻元朝，在南京建立明朝。為鞏固政權，他採取了一系列措施：恢復科舉制度，建立錦衣衛，實行高度中央集權。朱元璋還多次清洗功臣，鞏固皇權。明朝的建立標誌著漢族重新執掌中原政權，對中國歷史產生深遠影響。其特點包括：強調儒家思想，重視農業發展，實行海禁政策等。"
    student_output = "明朝的建立是由朱元璋領導的。他原本是個窮苦農民，加入了紅巾軍起義，最後成功推翻了元朝的統治。1368年，朱元璋在南京建立了明朝。為了鞏固政權，他採取了很多措施，比如恢復科舉制度、建立錦衣衛等。朱元璋還多次清洗功臣，鞏固自己的權力。明朝的建立，使漢族又一次成為中國的統治民族。"
    result = evaluate_student_output(prompt, chatgpt_output, student_output)
    print(json.dumps(result, indent=2, ensure_ascii=False))