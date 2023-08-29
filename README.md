# telegramBot

Представленный телеграмм-бот реагирует на команду /start и пишет приветственный ответ. После чего через меню кнопок предлагается выбрать одну из 3ёх возможностей. Бот предоставляет возможность: 
•	выделить аудио-дорожку из присланного видео-ряда;
•	из звукового ряда выделить информацию (кол-во сэмплов на секунду, частоту дискретизации, темп, бит с диаграммой, общая визуализация аудио, тепловая карта и её нормализация в хроматограмму, радужная диаграмма, спектральный центроид и спектральная ширина);
•	подмена аудио в исходном видео на заданном промежутке времени.
Все шаги для пользователя подробно описываются (как, в каком формате и порядке надо отправлять входные данные). В самой программе, из меню выбора, после выбранного действия, с помощью функции bot.register_next_step_handler происходит переход во вспомогательные функции методов(load_video; load_audio; first_step_load, second_step_load, third_step_load), где происходит загрузка всей необходимой информации, передача в основной метод(extract_audio; selection_inf; replace_audio_in_video) и удаление рабочих файлов с компьютера после их отработки с помощью os.remove.
