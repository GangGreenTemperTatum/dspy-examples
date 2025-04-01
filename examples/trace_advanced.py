import dspy
import random
import os
from typing import List

# 1. Define signatures
class GenerateQuery(dspy.Signature):
    """Generate a search query that builds upon the context to find new relevant information.
    The query should be different from previous queries."""
    context: str = dspy.InputField(desc="Information already gathered")
    question: str = dspy.InputField(desc="Original question")
    previous_queries: List[str] = dspy.InputField(desc="Previous search queries made")
    query: str = dspy.OutputField(desc="A new query that seeks additional information")

class Answer(dspy.Signature):
    """Answer the question based on retrieved passages."""
    context: List[str] = dspy.InputField()
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()

# 2. Create a simple RAG program with multiple hops
class MultiHopRAG(dspy.Module):
    def __init__(self, num_hops=2):
        super().__init__()
        self.num_hops = num_hops
        self.generate_query = dspy.Predict(GenerateQuery)
        self.answer = dspy.Predict(Answer)

    def forward(self, question):
        context = []
        current_question = question
        queries = [question]  # Store queries for evaluation

        for hop in range(self.num_hops):
            # Generate a search query for this hop
            query_pred = self.generate_query(
                context="\n".join(context),
                question=current_question,
                previous_queries=queries  # Pass the list of previous queries
            )
            queries.append(query_pred.query)

            # Mock retrieval - in a real system, you'd use a retriever
            retrieved = self.mock_retrieve(query_pred.query)
            context.append(retrieved)

        # Final answer based on all context
        answer_pred = self.answer(context=context, question=question)
        return dspy.Prediction(answer=answer_pred.answer, queries=queries)

    def mock_retrieve(self, query):
        # Mock function that returns a relevant passage based on query
        passages = [
            "The first Olympic Games were held in Athens, Greece in 1896.",
            "Paris will host the 2024 Summer Olympics.",
            "Albert Einstein won the Nobel Prize in Physics in 1921.",
            "Marie Curie was the first person to win Nobel Prizes in two different sciences.",
            "The Earth orbits the Sun at an average distance of 93 million miles."
        ]
        return random.choice(passages)

# 3. Define examples
examples = [
    dspy.Example(question="When were the first modern Olympic Games held?"),
    dspy.Example(question="Who won the Nobel Prize in Physics in 1921?"),
    dspy.Example(question="What is the distance between Earth and the Sun?")
]

# 4. Define a validation function that uses both approaches
def validate_hops(example, pred):
    """Validate if the hops are good quality."""
    # Get queries directly from prediction
    queries = pred.queries

    # Check if any query is too long
    if max([len(q) for q in queries]) > 100:
        return False

    # Check if later queries are too similar to earlier ones
    for idx in range(2, len(queries)):
        current_query = queries[idx].lower()
        for prev_idx in range(idx):
            prev_query = queries[prev_idx].lower()

            # Calculate word overlap similarity
            current_words = set(current_query.split())
            prev_words = set(prev_query.split())

            if len(current_words) == 0 or len(prev_words) == 0:
                continue

            # Calculate similarity
            intersection = len(current_words.intersection(prev_words))
            smaller_set_size = min(len(current_words), len(prev_words))
            similarity = intersection / smaller_set_size

            if similarity > 0.8:
                return False

    return True

# 5. Configure DSPy with an OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

lm = dspy.LM("openai/gpt-4o-mini", api_key=OPENAI_API_KEY)
dspy.settings.configure(lm=lm)

# 6. Create and test the program
rag = MultiHopRAG(num_hops=3)

# Evaluation loop
for example in examples:
    # Get prediction with stored queries
    pred = rag(example.question)

    # Validate the hops
    is_valid = validate_hops(example, pred)

    # Print results
    print(f"Question: {example.question}")
    print(f"Answer: {pred.answer}")
    print(f"Valid hops: {is_valid}")

    # Print the hop queries
    for i, query in enumerate(pred.queries):
        if i == 0:
            print(f"Original question: {query}")
        else:
            print(f"Hop {i} query: {query}")
    print("-" * 50)