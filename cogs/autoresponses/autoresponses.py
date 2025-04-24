from discord.ext import commands
import random
import time
import pytz
from datetime import datetime

class AutoResponses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.greetings = self.load_greetings()
        self.facts = self.load_facts()
        print("AutoResponses cog loaded")

    def load_greetings(self):
        try:
            with open("data/greetings.txt", "r", encoding="utf-8") as file:
                return [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            print("Warning: data/greetings.txt not found. Using default greetings.")
            return [
                "hey there, {}!",
                "hello, {}!",
                "hi, {} how's it going",
                "yo, {}"
            ]
    
    def load_facts(self):
        try:
            with open("data/funfacts.txt", "r", encoding="utf-8") as file:
                return [line.strip() for line in file if line.strip()]
        except FileNotFoundError:
            print("Warning: data/funfacts.txt not found. Using default facts.")
            return [
                "Did you know? Honey never spoils.",
                "Bananas are berries, but strawberries aren't.",
                "A group of flamingos is called a 'flamboyance'.",
                "Octopuses have three hearts."
            ]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return  # Avoid responding to itself
        
        cst = pytz.timezone('US/Central')
        current_time = datetime.now(cst)
        lower_content = message.content.lower()
        
        morning_responses = [
            "good morning, {}! Hope you have a great day!",
            "Rise and shine, {}!",
            "Morning, {}! Have you had your coffee yet?",
            "Top of the morning to you, {}!"
        ]
        
        if 6 <= current_time.hour < 12:
            if any(phrase in lower_content for phrase in ["hi reece", "hello reece", "gm reece", "good morning reece"]):
                response = random.choice(morning_responses).format(message.author.mention)
                await message.channel.send(response)
            
        else:
            if any(phrase in lower_content for phrase in ["hi reece", "hello reece"]):
                response = random.choice(self.greetings).format(message.author.mention)
                await message.channel.send(response)
        
        if "do a backflip reece" in lower_content or "reece do a backflip" in lower_content:
            await message.channel.send("🤸")
            time.sleep(0.5)
            await message.channel.send("Ta-da!")
        
        if "fuck you reece" in lower_content:
            await message.channel.send("One should always aim high. Set your aspirations beyond your reach and you will always have something to strive for.")
        
        if "tell me a joke reece" in lower_content:
            jokes = [
                "Why don't programmers like nature? It has too many bugs!",
                "What do you call 8 hobbits? A hob-byte!",
                "Why did the computer catch a cold? It left its Windows open!",
                "I told my wife she should embrace her mistakes. She gave me a hug."
            ]
            await message.channel.send(random.choice(jokes))

        if "gn reece" in lower_content or "good night reece" in lower_content or "goodnight reece" in lower_content:
            await message.channel.send("Good night, {}".format(message.author.mention))
        
        if "what's your favorite color reece" in lower_content or "reece what is your favorite color" in lower_content or "what is your favorite color reece" in lower_content:
            await message.channel.send("I like #00FF00, it's a very refreshing shade of green!")
        
        if "who made you reece" in lower_content:
            await message.channel.send("I was created by some wonderful humans with way too much time on their hands!")
        
        if "reece tell me a fun fact" in lower_content or "tell me a fun fact reece" in lower_content:
            await message.channel.send(random.choice(self.facts))

async def setup(bot):
    await bot.add_cog(AutoResponses(bot))
