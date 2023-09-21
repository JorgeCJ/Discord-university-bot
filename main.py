import discord
from discord import app_commands
import random
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

id_server =  #Enter your server ID here

cred = credentials.Certificate('')#firebase settings
firebase_admin.initialize_app(cred)

db = firestore.client()

user_registers = {}

class client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False
        self.register_numbers = set()

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(id=id_server))
            self.synced = True
        print(f"We entered as {self.user}.")

    async def close(self):
        for user_id, register_data in user_registers.items():
            number = register_data['number']
            date = register_data['date'].isoformat()
            full_name = register_data['full_name']
            document = register_data['document']
            db.collection('registers').document(str(user_id)).set({
                'number': number,
                'date': date,
                'full_name': full_name,
                'document': document
            })

        await super().close()

    def get_next_register_number(self):
        if self.register_numbers:
            next_register_number = max(self.register_numbers) + 1
        else:
            next_register_number = random.randint(1111111111, 999999999999)
        self.register_numbers.add(next_register_number)
        return next_register_number

aclient = client()
tree = app_commands.CommandTree(aclient)

docs = db.collection('registers').stream()
for doc in docs:
    user_id = int(doc.id)
    data = doc.to_dict()
    register_data = {
        'number': data['number'],
        'date': datetime.datetime.fromisoformat(data['date']),
        'full_name': data['full_name'],
        'document': data['document']
    }
    user_registers[user_id] = register_data
    aclient.register_numbers.add(data['number'])

@tree.command(guild=discord.Object(id=id_server), name='register', description='Gives the register Number')
async def slash_register(interaction: discord.Interaction, full_name: str, document: str):
    user_id = interaction.user.id

    if user_id in user_registers:
        previous_date = user_registers[user_id]['date']
        expiration_date = previous_date + datetime.timedelta(days=365 * 5)
        if datetime.datetime.now() > expiration_date:
            await interaction.response.send_message("Valid diploma and degree completed.", ephemeral=True)
        else:
            time_remaining = expiration_date - datetime.datetime.now()
            await interaction.response.send_message(f"Registration already completed, and there are still {time_remaining.days} days left for the validation of the diploma.\n\nFull Name: {user_registers[user_id]['full_name']}\nDocument: {user_registers[user_id]['document']}", ephemeral=True)
    else:
        if len(aclient.register_numbers) >= 999999999999:
            next_register_number = max(aclient.register_numbers) + 1
            register_data = {
                'number': next_register_number,
                'date': datetime.datetime.now(),
                'full_name': full_name,
                'document': document
            }
            user_registers[user_id] = register_data

            date = register_data['date'].isoformat()
            db.collection('registers').document(str(user_id)).set({
                'number': next_register_number,
                'date': date,
                'full_name': full_name,
                'document': document
            })

            await interaction.response.send_message(f"No more random numbers available. Registered with the next number: {next_register_number}", ephemeral=True)
        else:
            number_register = aclient.get_next_register_number()
            register_data = {
                'number': number_register,
                'date': datetime.datetime.now(),
                'full_name': full_name,
                'document': document
            }
            user_registers[user_id] = register_data

            date = register_data['date'].isoformat()
            db.collection('registers').document(str(user_id)).set({
                'number': number_register,
                'date': date,
                'full_name': full_name,
                'document': document
            })

            await interaction.response.send_message(f"Register {number_register}", ephemeral=True)

@tree.command(guild=discord.Object(id=id_server), name='validate', description='Validates the register')
async def slash_validate(interaction: discord.Interaction, register_number: int):
    if any(register_number == v['number'] for v in user_registers.values()):
        user_id = next((k for k, v in user_registers.items() if v['number'] == register_number), None)

        if user_id:
            register_data = user_registers[user_id]
            previous_date = register_data['date']
            expiration_date = previous_date + datetime.timedelta(days=365 * 5)
            if datetime.datetime.now() > expiration_date:
                await interaction.response.send_message("Valid diploma and degree completed.", ephemeral=True)
            else:
                time_remaining = expiration_date - datetime.datetime.now()
                full_name = register_data['full_name']
                document = register_data['document']
                await interaction.response.send_message(f"There are still {time_remaining.days} days left for graduation completion and diploma validation.\n\nFull Name: {full_name}\nDocument: {document}", ephemeral=True)
        else:
            await interaction.response.send_message("Register not found.", ephemeral=True)
    else:
        await interaction.response.send_message("Invalid register number.", ephemeral=True)
  

aclient.run('') #Bot authentication token