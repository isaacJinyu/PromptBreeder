import random
import re
from pb.types import Population, EvolutionUnit
from langchain.llms.base import BaseLLM
from typing import List
from sentence_transformers import SentenceTransformer, util
from pb.mutation_prompts import mutation_prompts
from pb.thinking_styles import thinking_styles
from pb import gsm

gsm8k_examples = gsm.read_jsonl('pb/data/gsm.jsonl')

# need below for estimation_distribution_mutation, not currently using.
# model = SentenceTransformer('multi-qa-distilbert-cos-v1')
# print(model) 

# Direct Mutation mutators
def zero_order_prompt_gen(unit: EvolutionUnit, problem_description: str, model: BaseLLM, **kwargs) -> EvolutionUnit:
    """Generates a new task-prompt P by concatenating the problem description D with the prompt 
    'a list of 100 hints:'. New task-prompt P is the first generated hint.
    
    Returns: 
        EvolutionUnit: the evolution unit to replace the loser unit.
    """
    result = model(problem_description + " A list of 100 hints: ")
    # search for the pattern "anything after 1. and before 2."
    pattern = r"1\.(.*?)2\."
    match = re.search(pattern, result, re.DOTALL)
    if match: 
        # return the first match
        unit.P = match.group(1).strip()
    else: 
        unit.P = ""
    
    return unit 

def first_order_prompt_gen(unit: EvolutionUnit, model: BaseLLM, **kwargs) -> EvolutionUnit:
    """Concatenate the mutation prompt M to the parent task-prompt P and pass it to the LLM to produce P'
    
    Returns: 
        EvolutionUnit: the evolution unit to replace the loser unit.
    """
    unit.P = model(unit.M + " " + unit.P) 
    return unit
    
# Estimation of Distribution Mutation - there is a variation of this called EDA rank
# and index mutation. I didn't implement it.
def estimation_distribution_mutation(unit: EvolutionUnit, population_units: List[EvolutionUnit], **kwargs) -> EvolutionUnit:
    """ Provide a filtered and numbered list of the current population of task-prompts to the LLM and ask it to continue this list with new task-prompts.
    The List is filtered via ensuring that no two task-prompts have a score of >0.95 via BERT embedding cosine similarities.
    The List is randomly ordered.  

    NOTE: I am confused by this one. Does this mutate the entire population? What values of the continued list from the LLM do I use as prompts? randomly sampled?
    Not going to implement this one yet. Maybe should email someone. 
    
    Returns: 
        EvolutionUnit: the evolution unit to replace the loser unit.
    """
    pass
def lineage_based_mutation(unit: EvolutionUnit, elites: List[EvolutionUnit], model: BaseLLM, **kwargs) -> EvolutionUnit:
    """Using the stored history of best units, provide the LLM this list in chronological order to produce a novel prompt as continuation.
    
    Returns: 
        EvolutionUnit: the evolution unit to replace the loser unit.
    """
    HEADING = "GENOTYPES FOUND IN ASCENDING ORDER OF QUALITY \n "
    # made a choice not to format it with newlines, could change later.
    ITEMS = ["{}. {}".format(i+1, x.P) for i, x in enumerate(elites)]
    unit.P = model(HEADING + ITEMS)
    
    return unit

# Hypermutation
def zero_order_hypermutation(unit: EvolutionUnit, problem_description: str, model: BaseLLM, **kwargs) -> EvolutionUnit:
    """ Concatenate the original problem_description to a randomly sampled thinking-style and feed it to the LLM to generate a new mutation-prompt.
    
    Returns: 
        EvolutionUnit: the evolution unit to replace the loser unit.
    """
    RANDOM_THINKING_STYLE = random.sample(thinking_styles, 1)
    unit.M = model(problem_description + RANDOM_THINKING_STYLE)
    return unit

def first_order_hypermutation(unit: EvolutionUnit, model: BaseLLM, **kwargs) -> EvolutionUnit:
    """ Concatenate the hyper-mutation prompt "Please summarize and improve the following instruction:"
    to a mutation-prompt to that the LLM generates a new mutation-prompt. This new mutation-prompt is then 
    instantly applied to the task-prompt of that unit.

    Returns: 
        EvolutionUnit: the evolution unit to replace the loser unit.
    """
    HYPER_MUTATION_PROMPT="Please summarize and improve the following instruction: "
    unit.M = model(HYPER_MUTATION_PROMPT + unit.M)
    unit.P = model(unit.M + " " + unit.P)
    return unit 


# Lamarckian Mutation
def working_out_task_prompt(unit: EvolutionUnit, model: BaseLLM, **kwargs) -> EvolutionUnit:
    """ A 'lamarckian' mutation operator similar to instruction induction in APE.

    As far as I can understand, give it both the Q and A from the gsm8k dataset, 
    concatenated between 'I gave a friend an instruction and some advice. Here
    are the correct examples of his workings out ' and 'The instruction was: '
    The idea is to let the LLM reverse-engineer the task-prompt.

    Returns: 
        EvolutionUnit: the evolution unit to replace the loser unit.
    """
    RANDOM_WORKING_OUT = random.sample(gsm8k_examples, 1)
  
    unit.P = model("I gave a friend an instruction and some advice. Here are the correct examples of his workings out " + RANDOM_WORKING_OUT['question'] +  RANDOM_WORKING_OUT['answer'] + " The instruction was: ")
    
# Prompt crossover and context shuffling
def prompt_crossover(**kwargs):
    """

    Returns: 
        EvolutionUnit: the evolution unit to replace the loser unit.
    """
def context_shuffling(**kwargs):
    """
    
    Returns: 
        EvolutionUnit: the evolution unit to replace the loser unit.
    """

# omitting the estimation_distribution_mutation
MUTATORS = [
    zero_order_prompt_gen,
    first_order_prompt_gen,
    lineage_based_mutation,
    zero_order_hypermutation,
    first_order_hypermutation,
    working_out_task_prompt,
    prompt_crossover,
    context_shuffling
]

def mutate(population: Population, model: BaseLLM):
    """Select and apply a random mutator"""
    # steps
    # 1. parse through the population, grouping each evo unit by 2
    # 2. for each pair of evo units, using a uniform distribution, select a random mutator (of the 9)
    # 3. mutate and populate population.units
    data = {
        'model' : model,
        'problem_description': population.problem_description,
        'mutator_prompt_one': "this should not be called."
    }
    result = zero_order_prompt_gen(**data)
