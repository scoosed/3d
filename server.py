import socket
from _thread import *
import pickle
import random

# --- Server Configuration ---
server_ip = "127.0.0.1" 
port = 5555

# --- Server Setup ---
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.bind((server_ip, port))
except socket.error as e:
    print(str(e))
    exit()

GRASS_GREEN = (124, 252, 0)

# --- Game State Management ---
players = {}
player_id_counter = 1
world_cubes = []

def generate_random_world_cubes(count=30):
    """
    Generates a set of randomly positioned and sized cubes on the main platform.
    This runs once when the server starts.
    """
    print(f"Generating {count} random cubes for the world...")
    
    # Generate ground
    world_cubes.append({'pos': (0, -2, 0), 'size': (150, 1, 150), 'color': GRASS_GREEN})
    
    for _ in range(count):
        # Ground plane is at y=-2, size=1, so top surface is at y=-1.5
        # Place cubes within the 150x150 ground plane area
        px = random.uniform(-70, 70) 
        pz = random.uniform(-70, 70)
        size = random.uniform(3, 10)
        # Position the cube so its bottom rests on the ground plane
        py = -1.5 + (size / 2) 
        
        color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
        
        world_cubes.append({'pos': (px, py, pz), 'size': size, 'color': color})

# --- Main Server Logic ---
def threaded_client(conn: socket.socket, player_id: int):
    """
    Handles communication with a single client in its own thread.
    """
    global players
    
    # 1. Send the new player their assigned ID
    conn.send(pickle.dumps(player_id))
    
    # 2. Receive the player's name from the client
    try:
        player_name = pickle.loads(conn.recv(2048))
    except (pickle.UnpicklingError, EOFError):
        print(f"Player {player_id} failed to send name. Disconnecting.")
        conn.close()
        return

    # 3. Create the initial state for the new player
    player_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    players[player_id] = {'pos': [0, 5, 0], 'color': player_color, 'name': player_name}
    print(f"Player '{player_name}' (ID: {player_id}) connected.")

    # 4. Main loop to receive updates from client and send back the world state
    while True:
        try:
            # Receive the client's current position data
            data = pickle.loads(conn.recv(2048))
            
            # Update this player's state on the server
            players[player_id]['pos'] = data['pos']

            if not data:
                break
            
            # <<< MODIFIED: Send back a dictionary containing BOTH players and world cubes
            reply = {
                'players': players,
                'cubes': world_cubes
            }
            conn.sendall(pickle.dumps(reply))

        except (pickle.UnpicklingError, ConnectionResetError, EOFError):
            break
            
    # 5. Cleanup when a player disconnects
    print(f"Player '{players.get(player_id, {}).get('name', 'Unknown')}' (ID: {player_id}) disconnected.")
    if player_id in players:
        del players[player_id]
    conn.close()

# --- Main Server Loop ---
generate_random_world_cubes()
s.listen()
print(f"Server Started. Listening on {server_ip}:{port}")

while True:
    conn, addr = s.accept()
    print(f"New connection from: {addr}")
    
    start_new_thread(threaded_client, (conn, player_id_counter))
    player_id_counter += 1