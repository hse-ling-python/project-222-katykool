import asyncio
import logging
import random
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import F
from gensim.models import KeyedVectors
from pymorphy2 import MorphAnalyzer
import wget
from aiogram.client.session.aiohttp import AiohttpSession

morph = MorphAnalyzer()

# открываем файлы с лексикой и модель (для рассчета векторной близости)
print('download start')
noun_m = wget.download("https://github.com/hse-ling-python/project-222-katykool/raw/main/noun_model.txt") # большие файлы не загружаются
print('download end')
#на pythonanywhere, поэтому придется загрузить модель прям в коде
print('model start')
noun_model = KeyedVectors.load_word2vec_format(noun_m, binary=False)
print('model end')
fn = open("freq_nouns.txt", encoding="utf-8")
fan = open("all_nouns.txt", encoding="utf-8")
freq_nouns = [x.strip() for x in fn.readlines()] # частотные существительные русского языка
all_nouns = [x.strip() for x in fan.readlines()] # все существительные, зафиксированные в модели


# включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
with open ("api.txt") as api:
    API_TOKEN = api.read()

# инициализируем бот
session = AiohttpSession(proxy="http://proxy.server:3128")
bot = Bot(token=API_TOKEN, session=session)

# и диспетчер
dp = Dispatcher()

# создаем состояние игры
class GuessingStates(StatesGroup):
    game_started = State()

# запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

@dp.message(Command("start")) # по команде /start запускается приветствие
async def main_page(message: types.Message):

    kb = [
    [
        types.KeyboardButton(text="Узнать больше о боте"),
        types.KeyboardButton(text="Инструкция"),
        types.KeyboardButton(text="Играть")
    ],
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer ("Привет! Меня зовут vecGuessr, и я векторная модель. Хочешь залезть в мои мысли и проверить, умеешь ли ты думать так же? Давай сыграем в игру! Чтобы узнать правила, нажми кнопку \"Инструкция\". Если хочешь сразу начать игру, нажми кнопку \"Играть\". Чтобу узнать подробнее обо мне и моей матери, нажми \"Узнать больше о боте\"!", reply_markup=keyboard)

@dp.message(F.text.lower() == "назад") # по тексту "назад" бот возвращается в главное меню
async def back(message: types.Message):

    kb = [
    [
        types.KeyboardButton(text="Узнать больше о боте"),
        types.KeyboardButton(text="Инструкция"),
        types.KeyboardButton(text="Играть")
    ],
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer ("Привет! Меня зовут vecGuessr, и я векторная модель. Хочешь залезть в мои мысли и проверить, умеешь ли ты думать так же? Давай сыграем в игру! Чтобы узнать правила, нажми кнопку \"Инструкция\". Если хочешь сразу начать игру, нажми кнопку \"Играть\". Чтобу узнать подробнее обо мне и моей матери, нажми \"Узнать больше о боте\"!", reply_markup=keyboard)

@dp.message(F.text.lower() == "инструкция") # по тексту "инструкция" запускается инструкция
async def instruction(message: types.Message, state: FSMContext):
    kb = [
       [
           types.KeyboardButton(text="Назад"),
           types.KeyboardButton(text="Играть")
       ],
   ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer ("Сейчас я расскажу тебе правила игры. Но сначала предыстория. \n\n Как ты уже знаешь, я -- векторная модель. Это значит, что значения слов я представляю в виде наборов чисел -- векторов -- существующих во много-много-многомерном пространстве. Например, похожие слова находятся рядом, а непохожие -- далеко. \n\n Так как я полностью основана на числах, то я умею проводить \"арифметические операции\" над словами. Вот пример. Как думаешь, что будет, если сложить король + женщина? Правильно, будет королева! \n\n Давай сыграем в векторную арифметику: я спрошу, что будет, если сложить два слова, а ты отправь мне ответ сообщением. Я скажу тебе, насколько далеко ты от ответа: чем меньше процент, тем ты ближе! Количество попыток неограничено. \n Чтобы сдаться, отправь мне \"/stop\". Если захочешь вернуться в главное меню, нажми кнопку Назад, а если хочешь сейчас начать игру, нажми Играть. \n\n Ну что, поехали?", reply_markup=keyboard)

@dp.message(F.text.lower() == "узнать больше о боте") # по тексту "узнать больше о боте" запускается информация о боте
async def about (message: types.Message, state: FSMContext):
    kb = [
       [
           types.KeyboardButton(text="Назад"),
       ],
   ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer ('Этот бот -- проект по программированию студентки второго курса ФиКЛа Вышки Кати Шерстневой. Если вы хотите связаться с разработчицей бота, напишите @katykool. Бот основан на векторной модели <b>word2vec</b>. Читайте подробнее на страничке проекта на <a href="https://github.com/hse-ling-python/project-222-katykool">гитхабе</a>', parse_mode='HTML', reply_markup=keyboard)

@dp.message(F.text.lower() == "играть") # по тексту "играть" запускается игра
async def question(message: types.Message, state: FSMContext):

    q_words = random.choices(freq_nouns, k=2) # генерация двух рандомных слов
    q = noun_model.most_similar(positive=q_words, topn=1) # вычисление вектора, ближайшего к сумме векторов загаданных слов (т.е. ответ)
    # проверка на то, чтобы получившийся вектор не был слишко близко к какому-либо из загаданных векторов (чтобы избежать случаев типа окно+экран=телеэкран)
    # если косинусное расстояние между ответ-вектором и каким-либо из загаданных больше 0.6, то пара перевыбирается
    cos_one = noun_model.similarity(q[0][0], q_words[0])
    cos_two = noun_model.similarity(q[0][0], q_words[1])
    while cos_one > 0.6 or cos_two>0.6:
        q_words = random.choices(freq_nouns, k=2) # генерация двух рандомных слов
        q = noun_model.most_similar(positive=q_words, topn=1) # вычисление вектора, ближайшего к сумме векторов загаданных слов (т.е. ответ)
        cos_one = noun_model.similarity(q[0][0], q_words[0])
        cos_two = noun_model.similarity(q[0][0], q_words[1])

    await state.set_data({'words': q_words, 'answer': q}) # сохраняем данные
    await state.set_state(GuessingStates.game_started) # запускаем игровое состояние

    await message.answer (f'Что будет, если сложить слова {q_words[0]} и {q_words[1]}?')

@dp.message(Command('stop'), StateFilter(GuessingStates.game_started)) # по команде /stop игра прекращается: бот выходит из игрового состояния и выдает ответ
async def stop(message: types.Message, state: FSMContext):
    q = await state.get_data()
    q = q['answer']

    await state.clear()
    await message.answer(f"Эх, жаль, что ты сдаешься. Правильный ответ -- {q[0][0]}. Приходи играть еще. Для новой игры нажми кнопку Играть")

@dp.message(F.text, StateFilter(GuessingStates.game_started)) # ловит сообщение пользователя и считает косинусное расстояние между ним и настоящим ответом
async def answer(message: types.Message, state: FSMContext):
    global q_words, q, all_nouns, noun_model, freq_nouns

    q = await state.get_data()
    q = q['answer']

    m = message.text.strip().lower()

    if m in all_nouns:
        cos = noun_model.similarity(q[0][0], m) # косинусное расстояние между ответом пользователя и правильным ответом
        if m == q[0][0]:
            await message.answer ("Ты угадал! Чтобы сыграть снова, нажми кнопку Играть")
            await state.clear()
        else:
            if cos < 0.5:
                await message.answer (f"Далековато! Ты в {100 - round(100*cos)}% от правильного ответа\nЧтобы сдаться и узнать ответ, напиши мне /stop") # проценты -- для более простого осознания происходящего для пользователя.
                # это просто косинусное расстояние, переведенное в проценты.
            else:
                await message.answer (f"Близко! Ты в {100 - round(100*cos)}% от правильного ответа\nЧтобы сдаться и узнать ответ, напиши мне /stop")
    else:
        await message.answer("Прости, я не знаю такого слова. Попробуй еще раз!\nА чтобы сдаться и узнать ответ, напиши мне /stop") # если введенного пользователем слова нет в словаре

if __name__ == "__main__":
    asyncio.run(main())

fn.close()
fan.close()