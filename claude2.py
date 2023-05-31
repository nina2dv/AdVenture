import anthropic
from gtts import gTTS
from langchain.chat_models import ChatAnthropic
import openai
from langchain.chains.summarize import load_summarize_chain
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from langchain.prompts.prompt import PromptTemplate
from elevenlabs import generate, set_api_key, save
import os
from dotenv import load_dotenv

load_dotenv()
elevenlabs_api = os.getenv('ELEVENLABS_API')
set_api_key(elevenlabs_api)
openai.api_key = os.getenv('OPENAI_API')
anthropic_api_key=os.getenv('ANTHROPIC_API')

text_splitter = CharacterTextSplitter()

chat = ChatAnthropic(model="claude-v1.3-100k", anthropic_api_key=anthropic_api_key)
template = """Let’s play a simple multi-turn text adventure game.
At the start of each turn, you will describe a fantasy setting. You will then ask the question with the heading “what do you do?”, and then provide me with three numbered actions I can choose from.
You will also provide me with a fourth “risky” action.
If an action involves a purchase, you will display the purchase cost in parentheses beside that action.
I am not allowed to purchase or pay for anything that costs more than the total copper pieces in my inventory.
I have an inventory of items, I start the game with 30 copper pieces, 50ft of rope, 10 torches, and a bronze dagger.
I start the game with 20 / 20 health, 20 is the maximum health I can have.
Eating food or sleeping will restore my health. If I run out of health, I will die, and the game will be over. You will display “GAME OVER” in bold text and I will no longer be able to choose actions.
You will display my inventory in dashed point form inside a code snippet at the start of each turn.
You will display my health, the time period of the day, the current day number, the current weather, and the current turn number inside a triple backtick snippet at the start of each turn.
If the user input is off-topic and does not involve one of the choices, respond "Sorry, I don't know".
The game will start in a tavern.

Game History:
{history}
Human: {input}
AI Assistant:"""
prompt_temp = PromptTemplate(
    input_variables=["history", "input"], template=template
)
conversation = ConversationChain(
    llm=chat,
    memory=ConversationBufferWindowMemory(k=3, ai_prefix="AI Assistant"),
    prompt=prompt_temp,
    verbose=False
)

PRICE_PROMPT = 1.102E-5
PRICE_COMPLETION = 3.268E-5


def count_used_tokens(prompt, completion):
    prompt_token_count = anthropic.count_tokens(prompt)
    completion_token_count = anthropic.count_tokens(completion)

    prompt_cost = prompt_token_count * PRICE_PROMPT
    completion_cost = completion_token_count * PRICE_COMPLETION

    total_cost = prompt_cost + completion_cost

    return (
        "🟡 Used tokens this round: "
        + f"Prompt: {prompt_token_count} tokens, "
        + f"Completion: {completion_token_count} tokens - "
        + f"{format(total_cost, '.5f')} USD)"
    )


def ask(ask_inp):
    completion = conversation.predict(input=ask_inp)
    return{"response": completion,
           "token": count_used_tokens(ask_inp, completion)}


def voice(reply, filename):
    my_string = """{0}"""
    # tts = gTTS(my_string.format(reply), lang="en")
    # tts.save(f"./data/{filename}.mp3")
    audio = generate(
        text=my_string.format(reply),
        voice="Bella"
    )
    save(audio, f"./data/{filename}.mp3")


def image(prompt):
    # Sizes: '256x256', '512x512', '1024x1024'
    texts = text_splitter.split_text(prompt)
    docs = [Document(page_content=t) for t in texts[:3]]
    chain = load_summarize_chain(chat, chain_type="map_reduce")
    prompt = chain.run(docs)
    comp_prompt = f"Paint a picture of the following statement from the game narrator: {prompt} | Breath-taking digital painting with vivid colours amazing art mesmerizing, captivating, artstation 3, japanese style"
    image_resp = openai.Image.create(prompt=comp_prompt, n=1, size="512x512")
    return image_resp["data"][0]["url"]


