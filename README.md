[![wakatime](https://wakatime.com/badge/user/90c8afe4-47c1-4f14-9423-4474ab0618ae/project/b7f2a6f9-be1b-4d8c-95f3-ab3fad720d9f.svg)](https://wakatime.com/badge/user/90c8afe4-47c1-4f14-9423-4474ab0618ae/project/b7f2a6f9-be1b-4d8c-95f3-ab3fad720d9f)
## Installing dependencies
Make sure you have all the necessary libraries listed in the `requirements.txt` file. Run the following command to install all dependencies:
```angular2html
pip install -r requirements.txt
```
## Configuring .env
In the root folder of the bot, there is a `.env` file where you need to specify the following information:
```dotenv
BOT_TOKEN="TOKEN" # Main bot token
TEST_BOT_TOKEN="TOKEN" # Test bot token
```
Set the appropriate values for each item.

## settings.py
In the `settings.py` file located in the `config` folder, there are certain parameters that need to be adjusted according to your preferences.
```python
test_mode = True  # Changes the database file name  
                  # and the bot token used to run the bot       
debug_mode = True
```

## Running the bot
Now that the dependencies are installed and the `.env` file is configured, you can run the bot. Use the following command:
```
python main.py
```