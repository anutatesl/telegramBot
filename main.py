import librosa
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from colorama import Fore
from sklearn import preprocessing
import librosa.display
from moviepy.editor import *

import telebot
from telebot import types


token = '6207774750:AAGfzAiTjPTweAY0SqH3FBZGBlTpZYdjE_w'
bot = telebot.TeleBot(token)

old_video = None
old_audio = None
new_video = None

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет ✌️ ")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton("/menu")

    markup.add(button)

    bot.send_message(message.from_user.id, 'Ну что, поехали?', reply_markup=markup)

@bot.message_handler(commands=['menu'])
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Выделение аудио')
    btn2 = types.KeyboardButton('Подмена аудио')
    btn3 = types.KeyboardButton('Выделение информации аудио-ряда')

    markup.add(btn1, btn2, btn3)

    bot.send_message(message.from_user.id, 'Что мне надо сделать?', reply_markup=markup)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    #chat_id = message.chat.id
    if message.text == 'Подмена аудио':
        msg = bot.reply_to(message, 'Отправьте по очереди: '
                                    '\n1. Видео-файл с разрешением "*.mp4": '
                           '\n2. Аудио-файл, который необходимо вставить с разрешением "*.mp3"'
                           '\n3. Интервал через запятую в секундах. Например: "3 20", будет означать, '
                                    'что изменится аудио-часть с 3 по 20 секунду в видео'
                                    '\n\n Вначале видео😉')
        bot.register_next_step_handler(msg, first_step_load)

    elif message.text == 'Выделение аудио':
        msg = bot.reply_to(message, 'Загрузите видео-файл с разрешением "*.mp4": ')
        bot.register_next_step_handler(msg, load_video)

    elif message.text == 'Выделение информации аудио-ряда':
        msg = bot.reply_to(message, 'Загрузите аудио-файл с разрешением "*.ogg": ')
        bot.register_next_step_handler(msg, load_audio)

    else:
        bot.send_message(message.from_user.id, 'Проверьте, что Ваш выбор соответствует диапазону')

def load_video(message):
    chat_id = message.chat.id
    try:
        file_details = message.video
        bot.send_message(chat_id, 'Загрузка видео...')
        file_id = file_details.file_id
        file_info = bot.get_file(file_id)
        downloaded_video = bot.download_file(file_info.file_path)
        source_file_name = message.video.file_id + ".mp4"
        with open(source_file_name, 'wb') as saved_file:
            saved_file.write(downloaded_video)
        destination_file_name = 'audio.mp3'

        bot.send_message(chat_id, "Выделяю аудио... ")
        extract_audio(source_file_name, destination_file_name)
        audio = open(destination_file_name, 'rb')
        bot.send_audio(chat_id, audio)
        audio.close()
        os.remove(source_file_name)
        os.remove(destination_file_name)
    except:
        bot.send_message(chat_id, 'Упс, произошла ошибка. Пожалуйста, попробуйте ещё раз!')
        return

def extract_audio(source_file_name, destination_file_name):
    mp4file, mp3file = source_file_name, destination_file_name
    video_clip = VideoFileClip(mp4file)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(mp3file)
    video_clip.close()

def load_audio(message):
    chat_id = message.chat.id
    try:
        file_details = message.audio
        bot.send_message(chat_id, 'Загрузка audio...')
        file_id = file_details.file_id
        file_info = bot.get_file(file_id)
        downloaded_audio = bot.download_file(file_info.file_path)
        source_file_name = message.audio.file_id + ".ogg"
        with open(source_file_name, 'wb') as saved_file:
            saved_file.write(downloaded_audio)

        msg = bot.send_message(chat_id, "Выделяю информацию... ")
        selection_inf(msg, source_file_name)
        os.remove(source_file_name)

    except:
        bot.send_message(chat_id, 'Упс, произошла ошибка. Пожалуйста, попробуйте ещё раз!')
        return

def selection_inf(message, source_file_name):

    sample_rate, sr = librosa.load(source_file_name)
    bot.send_message(message.chat.id,
                     "Кол-во сэмплов на секунду и частота дискретизации: " + str(sample_rate.shape) + " " + str(sr))

    tempo, beat = librosa.beat.beat_track(y=sample_rate, sr=sr)
    bot.send_message(message.chat.id, "Темп(скорость, с которой паттерны повторяются)бит/мин: " + str(tempo))
    bot.send_message(message.chat.id, "Бит(отрезок времени, ритм, выстукиваемый в песне): " + str(beat))

    #Разделение гармонических (тональных ) и ударных (переходных) сигналов на две формы волны
    #Вывод битов в виде диаграммы
    y_harmonic, y_percussive = librosa.effects.hpss(sample_rate)
    tempo, beat_frames = librosa.beat.beat_track(y=y_percussive, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    beat_time_diff = np.ediff1d(beat_times)
    beat_nums = np.arange(1, np.size(beat_times))
    fig, ax = plt.subplots()
    fig.set_size_inches(15, 5)
    ax.set_ylabel("Time difference (s)")
    ax.set_xlabel("Beats")
    g = sns.barplot(x=beat_nums, y=beat_time_diff, palette="BuGn_d", ax=ax)
    g = g.set(xticklabels=[])
    plt.savefig('Visualization_audio.png')
    bot.send_photo(message.chat.id, open("Visualization_audio.png", 'rb'), caption=f"Диаграмма битов")
    os.remove("Visualization_audio.png")

    #Визуализация аудио
    fig, ax = plt.subplots()
    librosa.display.waveshow(sample_rate, sr=sr)
    ax.set(title='Visualization audio')
    plt.savefig('Visualization_audio.png')
    bot.send_photo(message.chat.id, open("Visualization_audio.png", 'rb'), caption=f"Визуализация аудио")
    os.remove("Visualization_audio.png")

    #Мел-кепстральные коэффициенты(MFCC)
    #-матрица значений, которая захватывает тембральные аспекты музыкального инструмента
    #Тепловая карта
    mfcc = librosa.feature.mfcc(y=sample_rate, sr=sr, hop_length=8192, n_mfcc=12)
    mfcc_delta = librosa.feature.delta(mfcc)
    sns.heatmap(mfcc_delta)
    plt.savefig('Visualization_audio.png')
    bot.send_photo(message.chat.id, open("Visualization_audio.png", 'rb'), caption=f"Тепловая карта")
    os.remove("Visualization_audio.png")
    #Нормализация тепловой карты в хроматограмму
    chromagram = librosa.feature.chroma_cqt(y=sample_rate, sr=sr)
    sns.heatmap(chromagram)
    plt.savefig('Visualization_audio.png')
    bot.send_photo(message.chat.id, open("Visualization_audio.png", 'rb'),
                   caption=f"Нормализация тепловой карты в хроматограмму")
    os.remove("Visualization_audio.png")

    #Rainbowgrams
    D = librosa.stft(sample_rate)
    mag, phase = librosa.magphase(D)
    freqs = librosa.fft_frequencies()
    times = librosa.times_like(D)

    phase_exp = 2*np.pi*np.multiply.outer(freqs,times)
    fig, ax = plt.subplots()
    img = librosa.display.specshow(np.diff(np.unwrap(np.angle(phase)-phase_exp, axis=1), axis=1, prepend=0),
                         cmap='hsv',
                         alpha=librosa.amplitude_to_db(mag, ref=np.max)/80 + 1,
                         ax=ax,
                         y_axis='log',
                         x_axis='time')
    ax.set_facecolor('#000')
    cbar = fig.colorbar(img, ticks=[-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
    cbar.ax.set(yticklabels=['-π', '-π/2', "0", 'π/2', 'π']);
    ax.set(title='Rainbowgram')
    plt.savefig('Visualization_audio.png')
    bot.send_photo(message.chat.id, open("Visualization_audio.png", 'rb'), caption=f"Радужная диаграмма")
    os.remove("Visualization_audio.png")

    #Спектральный центроид
    spectral_centroids = librosa.feature.spectral_centroid(y=sample_rate, sr=sr)[0]
    spectral_centroids.shape
    # Вычисление временной переменной для визуализации
    plt.figure(figsize=(12, 4))
    frames = range(len(spectral_centroids))
    t = librosa.frames_to_time(frames)
    # Нормализация спектрального центроида для визуализации
    def normalize(sample_rate, axis=0):
        return preprocessing.minmax_scale(sample_rate, axis=axis)
    # Построение спектрального центроида вместе с формой волны
    librosa.display.waveshow(sample_rate, sr=sr, alpha=0.4)
    plt.plot(t, normalize(spectral_centroids), color='b')
    plt.savefig('Visualization_audio.png')
    bot.send_photo(message.chat.id, open("Visualization_audio.png", 'rb'), caption=f"Спектральный центроид")
    os.remove("Visualization_audio.png")

    #Спектральная ширина
    spectral_bandwidth_2 = librosa.feature.spectral_bandwidth(y=sample_rate+0.01, sr=sr)[0]
    spectral_bandwidth_3 = librosa.feature.spectral_bandwidth(y=sample_rate+0.01, sr=sr, p=3)[0]
    spectral_bandwidth_4 = librosa.feature.spectral_bandwidth(y=sample_rate+0.01, sr=sr, p=4)[0]
    plt.figure(figsize=(15, 9))
    librosa.display.waveshow(sample_rate, sr=sr, alpha=0.4)
    plt.plot(t, normalize(spectral_bandwidth_2), color='r')
    plt.plot(t, normalize(spectral_bandwidth_3), color='g')
    plt.plot(t, normalize(spectral_bandwidth_4), color='y')
    plt.legend(('p = 2', 'p = 3', 'p = 4'))
    plt.savefig('Visualization_audio.png')
    bot.send_photo(message.chat.id, open("Visualization_audio.png", 'rb'), caption=f"Спектральная ширина")
    os.remove("Visualization_audio.png")
    bot.send_message(message.chat.id, "Готово!")

def first_step_load(message):
    global old_video
    chat_id = message.chat.id
    try:
        file_details = message.video
        bot.send_message(chat_id, 'Загрузка видео...')
        file_id = file_details.file_id
        file_info = bot.get_file(file_id)
        downloaded_video = bot.download_file(file_info.file_path)
        old_video = message.video.file_id + ".mp4"
        with open(old_video, 'wb') as saved_file:
            saved_file.write(downloaded_video)

        msg = bot.reply_to(message, 'Замечательно, теперь загрузите аудио-файл, '
                                    'который необходимо вставить с разрешением "*.mp3"')
        bot.register_next_step_handler(msg, second_step_load)
    except:
        bot.send_message(chat_id, 'Упс, произошла ошибка. Пожалуйста, попробуйте ещё раз!')
        return

def second_step_load(message):
    global old_audio

    chat_id = message.chat.id
    file_details = message.audio
    bot.send_message(chat_id, 'Загрузка audio...')
    file_id = file_details.file_id
    file_info = bot.get_file(file_id)
    downloaded_audio = bot.download_file(file_info.file_path)
    old_audio = message.audio.file_id + ".mp3"
    with open(old_audio, 'wb') as saved_file:
        saved_file.write(downloaded_audio)

    msg = bot.reply_to(message, 'Отправьте интервал через запятую в секундах. Например: "3 20", '
                                'будет означать,что изменится аудио-часть с 3 по 20 секунду в видео')
    bot.register_next_step_handler(msg, third_step_load)

def third_step_load(message):
    global new_video
    chat_id = message.chat.id
    numbers_str = message.text.lower()
    both_numbers = numbers_str.split(' ', 1)

    try:
        if not(both_numbers[0].isdigit()) or not(both_numbers[1].isdigit()):
            raise ValueError('Числа введены некорректно, прийдётся начать с начала😔'
                             '\nВыберете действие, которое хотите сделать: ')
    except Exception as error:
        bot.send_message(chat_id, str(error))
        os.remove(old_audio)
        os.remove(old_video)
        return

    start_value = int(both_numbers[0])
    end_value = int(both_numbers[1])

    new_video = "RESULT.mp4"

    bot.send_message(chat_id, "Соединяю... ")
    replace_audio_in_video(old_video, old_audio, new_video, start_value, end_value)

    result = open(new_video, 'rb')
    bot.send_video(chat_id, result)
    result.close()
    os.remove(old_audio)
    os.remove(new_video)
    os.remove(old_video)

def replace_audio_in_video(source_video_name, source_audio_name, new_video, start_value, end_value):
    global old_audio
    global old_video

    start_time, end_time = start_value, end_value
    mp4file, mp3file, result = source_video_name, source_audio_name, new_video
    video_clip = VideoFileClip(mp4file)
    audio_clip = AudioFileClip(mp3file)

    print(Fore.CYAN + '[+] Начинаю вырезку фрагмента видео')
    print(Fore.YELLOW + f'   - Длительность фрагмента: {end_time - start_time} секунд')
    print(Fore.YELLOW + f'   - Общая продолжительность видео: {video_clip.duration} секунд\n')

    clip_clip = video_clip.subclip(start_time, end_time)
    clip_before = video_clip.subclip(0, start_time)
    clip_after = video_clip.subclip(end_time, )
    clip_clip.audio = audio_clip
    clip_to_merge = [clip_before, clip_clip, clip_after]
    merge_final = concatenate_videoclips(clip_to_merge)
    merge_final.write_videofile(result)

    audio_clip.close()
    video_clip.close()

if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)