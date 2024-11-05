import asyncio

class ConnectionManager:
    def __init__(self):
        self.connections = set()

    async def broadcast_message(self, message):
        '''Broadcast a message to all connected clients.'''
        for connection in self.connections:
            try:
                await connection.send(message)
            except Exception as e:
                print(f"Error sending message: {e}")

    def add_connection(self, connection):
        self.connections.add(connection)

    def remove_connection(self, connection):
        self.connections.discard(connection)