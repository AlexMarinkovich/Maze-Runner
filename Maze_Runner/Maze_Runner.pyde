import random
import math
import pickle
add_library('minim')

def settings():
    global FPS, FPS_ratio, SF, max_name_length
    program_info = {}
    for line in read_file("program_info.txt"):
        program_info.update({line[0]: line[1]})
    
    FPS = program_info["FPS"]
    FPS_ratio = FPS // program_info["animation_FPS"]
    SF = program_info["SF"] / 100.0
    size(int(program_info["screen_width"]*SF), int(program_info["screen_height"]*SF))
    max_name_length = program_info["max_name_length"]
    
## resets global variables that need reseting after switching screens
def reset_variables():
    global player_name, leaderboards_scroll
    player_name = ""
    leaderboards_scroll = 0

def setup():
    global mode, mouse_clicked, mouse_scrolled, key_pressed, game_status, all_image_info, all_anim_info, all_sound_info, maze_info, move_key_states, move_key_order, highscores, Maze, Player
    
    all_image_info = {}
    for line in read_file("all_image_info.txt"):
        all_image_info.update({line[0]: loadImage(line[1])})
    
    all_anim_info = {}
    for line in read_file("all_animation_info.txt"):
        all_anim_info.update({line[0]: (loadImage(line[1]), line[2], line[3], line[4])})
    
    minim = Minim(this)
    all_sound_info = {}
    for line in read_file("all_sound_info.txt"):
        if line[2] == "sample":
            all_sound_info.update({line[0]: minim.loadSample(line[1])})
        elif line[2] == "file":
            all_sound_info.update({line[0]: minim.loadFile(line[1])})
        all_sound_info[line[0]].setGain(line[3])
    
    all_sound_info["music"].loop()
    
    maze_info = {}
    for line in read_file("maze_info.txt"):
        maze_info.update({line[0]: line[1]})
    
    move_key_states = {}
    move_key_order = {}
    for line in read_file("move_keys.txt"):
        move_key_states.update({line[1]: False, line[2]: False, line[3]: False, line[4]: False})
        move_key_order.update({line[0]: (line[1], line[2], line[3], line[4])})
    
    frameRate(FPS)
    mode = "selection"
    mouse_clicked = False
    mouse_scrolled = 0
    key_pressed = False
    
    try:
        highscores = pickle_read("highscores.txt")
    except EOFError:
        highscores = []
    game_status = False
    reset_variables()
    
    class Maze:
        def __init__(self, num_cols, num_rows, num_doors, door_flip_frequency):
            self.num_cols = num_cols
            self.num_rows = num_rows
            self.num_doors = num_doors
            self.frame_counter = 0
            self.door_flip_frequency = door_flip_frequency
            
        ## takes in the width and height of the maze, outputs a randomly generated maze
        def generate_maze(self):
            ## easier to make the borderless maze first, then add the borders later
            width = self.num_cols - 2
            height = self.num_rows - 2
            
            ## starts with a maze full of walls
            layout = [["w" for i in range(width)] for i in range(height)]
            
            ## chooses a random cell to start creating paths from
            starting_cell = random.randint(0, height-1)//2*2, random.randint(0, width-1)//2*2
            layout[starting_cell[0]][starting_cell[1]] = "p"
        
            ## takes in the original cell's position and the distance between the original and adjacent cells, outputs a list with tuples for each adjacent cell in the format (adjacent cell, original cell)
            def get_adj_cells(original_cell, distance):
                row = original_cell[0]
                col = original_cell[1]
                adj_cells = []
        
                if col >= distance:
                    north_cell = row, col - distance
                    if layout[north_cell[0]][north_cell[1]] == "w":
                        adj_cells.append((north_cell, original_cell))
        
                if row <= height-1 - distance:
                    east_cell = row+distance, col
                    if layout[east_cell[0]][east_cell[1]] == "w":
                        adj_cells.append((east_cell, original_cell))
        
                if col <= width-1 - distance:
                    south_cell = row, col+distance
                    if layout[south_cell[0]][south_cell[1]] == "w":
                        adj_cells.append((south_cell, original_cell))
        
                if row >= distance:
                    west_cell = row-distance, col
                    if layout[west_cell[0]][west_cell[1]] == "w":
                        adj_cells.append((west_cell, original_cell))
                
                ## gives adjacent cells a different state so they can't be called adjacent with a seperate path cell
                for cell in adj_cells:
                    layout[cell[0][0]][cell[0][1]] = "a"
        
                return adj_cells
        
            ## takes in a new cell's position and a pre-existing path cell's position, makes a line of path cells connecting them
            def connect_path(new_cell, path_cell):
                layout[new_cell[0]][new_cell[1]] = "p"
        
                midpoint_cell = [(new_cell[0]+path_cell[0])//2, (new_cell[1]+path_cell[1])//2]
                layout[midpoint_cell[0]][midpoint_cell[1]] = "p"
        
            ## list with tuples of the format (adjacent cell, cell that they are adjacent to)
            adj_cells = []
            adj_cells += (get_adj_cells(starting_cell, 2))
            
            ## constantly randomly generates paths that are not connected until the maze is filled
            while len(adj_cells) > 0:
                rand_adj_cell = random.choice(adj_cells)
                connect_path(rand_adj_cell[0], rand_adj_cell[1])
                adj_cells.remove(rand_adj_cell)
                adj_cells += (get_adj_cells(rand_adj_cell[0], 2))
        
            ## adds borders to the maze
            layout.insert(0, ["w" for i in range(width)])
            layout.append(["w" for i in range(width)])
            for row in layout:
                row.insert(0, "w")
                row += "w"
            
            self.layout = layout
        
        ## takes in the maze, puts a start point and an end point on the borders
        def make_start_end_points(self):
            
            ## randomly selects a position on the borders
            def get_edge_pos(rand_edge):
                if rand_edge == 1 or rand_edge == -1:
                    rand_col = random.randint(0, self.num_cols-2)//2*2 + 1
                    if rand_edge == 1:
                        rand_row = 0
                    else:
                        rand_row = self.num_rows-1
                else:
                    rand_row = random.randint(0, self.num_rows-2)//2*2 + 1
                    if rand_edge == 2:
                        rand_col = 0
                    else:
                        rand_col = self.num_cols-1
                
                return rand_row, rand_col
            
            ## adds a starting position and ending position to the maze
            rand_edge = random.choice([1,2,-1,-2]) # 1 is north edge, 2 is west edge, -1 is south edge, -2 is east edge 
            self.starting_pos = get_edge_pos(rand_edge)
            self.ending_pos = get_edge_pos(rand_edge*-1)
            self.layout[self.starting_pos[0]][self.starting_pos[1]] = "s"
            self.layout[self.ending_pos[0]][self.ending_pos[1]] = "e"
            
        ## takes in a maze and number of doors, selects certain random walls that connect paths to turn into doors to make possible alternative routes
        def make_doors(self):
            
            ## valid door positions are positions that connect different paths together
            valid_door_positions = []
            for i in range(1, self.num_rows-1):
                if i % 2 == 1:
                    for j in range(2, self.num_cols-2, 2):
                        if self.layout[i][j] != "p":
                            valid_door_positions.append((i,j))
        
                else:
                    for j in range(1, self.num_cols-1, 2):
                        if self.layout[i][j] != "p":
                            valid_door_positions.append((i,j))
        
            for i in range(self.num_doors):
                rand_door_pos = random.choice(valid_door_positions)
                self.layout[rand_door_pos[0]][rand_door_pos[1]] = "d"
                valid_door_positions.remove(rand_door_pos)
        
        ## takes in a maze, returns coordinates of the shortest path in a list
        def find_path(self, starting_pos):
            global shortest_path
            shortest_path = []
        
            ## finds every path to the end point and compares every possible path to find shortest path
            def DFS(i, j, path=[]):
                global shortest_path
                if i < 0 or j < 0 or i > len(self.layout)-1 or j > len(self.layout[0])-1:
                    return
                if self.layout[i][j] == "w" or self.layout[i][j] == "d" or (i, j) in path:
                    return
                if (i, j) == (self.ending_pos[0], self.ending_pos[1]):
                    if len(path) < len(shortest_path) or shortest_path == []:
                        path += [(i, j)]
                        shortest_path = path
                    return
                else:
                    DFS(i - 1, j, path + [(i, j)]) 
                    DFS(i + 1, j, path + [(i, j)])
                    DFS(i, j + 1, path + [(i, j)]) 
                    DFS(i, j - 1, path + [(i, j)])
                return
                
            DFS(starting_pos[0], starting_pos[1])
        
        ## gets a size in pixels for the cells of the maze so it fits on the screen no matter the maze's dimensions
        def calc_cell_size(self):
            if 500*SF / len(self.layout) < 650*SF / len(self.layout[0]):
                cell_size = 500*SF / len(self.layout)
            else:
                cell_size = 650*SF / len(self.layout[0])
            
            self.cell_size = int(cell_size)
        
        ## takes in the cell type, returns the screen positions of all the cells of a certain type in the maze
        def calc_cell_positions(self, cell_type):
            cell_positions = []
            
            for i in range(0, len(self.layout)):
                for j in range(0, len(self.layout[0])):
                    if self.layout[i][j] == cell_type:
                        cell_positions.append((j*self.cell_size, i*self.cell_size, i, j))
            
            return tuple(cell_positions)
        
        def create_door_info(self):
            self.door_info = []
            
            for door_pos in self.screen_door_positions:
                self.door_info.append([door_pos, "closed"])
        
        def display(self):
            noStroke()
            
            fill(0)
            for wall_pos in self.screen_wall_positions:
                rect(wall_pos[0], wall_pos[1], self.cell_size, self.cell_size)
            
            for door in self.door_info:
                if door[1] == "closed":
                    fill(255,0,0)
                else:
                    fill(150)
                rect(door[0][0], door[0][1], self.cell_size, self.cell_size)
            
            imageMode(CORNER)    
            image(all_image_info["finish_line_flag"], self.screen_ending_pos[0], self.screen_ending_pos[1], self.cell_size, self.cell_size)
        
        def flip_doors(self):
            if game_time >= 0:
                self.frame_counter += 1
            if self.frame_counter == self.door_flip_frequency:
                all_sound_info["door"].trigger()
                
                for door in self.door_info:
                    if door[1] == "closed" and random.randint(1,2) == 1:
                        door[1] = "open"
                        maze.layout[door[0][2]][door[0][3]] = "od"
                    
                    elif door[1] == "open":
                        door_can_close = True
                        
                        for player in Player.player_list:
                            if door[0][0]-self.cell_size*0.8 < player.x_pos < door[0][0]+self.cell_size*0.8 and door[0][1]-self.cell_size*0.8 < player.y_pos < door[0][1]+self.cell_size*0.8:
                                door_can_close = False
                        
                        if door_can_close:
                            door[1] = "closed"
                            maze.layout[door[0][2]][door[0][3]] = "d"
                
                self.frame_counter = 0
                
                if game_mode == "player vs computer":
                    self.find_path( (int(round(AI.maze_pos[0])), int(round(AI.maze_pos[1]))) )
                    shortest_path.insert(0, AI.maze_pos)
                    AI.path_index = 0
                    
                    ## if there's a straight line between these two points, delete the point in between to prevent ai from doing 2 u-turns in a row
                    if len(shortest_path) >= 3 and (shortest_path[0][0] == shortest_path[2][0] or shortest_path[0][1] == shortest_path[2][1]):
                        del shortest_path[1]
        
        
    class Player:
        def __init__(self, img, image_width, image_height, num_animation_frames, controls):
            Player.player_list.append(self)
            self.name = None
            self.image = img
            self.image_width = image_width
            self.image_height = image_height
            self.frame_counter = 0
            self.animation_frame = 0
            self.num_animation_frames = num_animation_frames
            self.frame_width = image_width // num_animation_frames
            self.controls = controls
            self.is_moving = False
            self.rotation = 0
            self.win_count = 0
            
        def display(self):
            imageMode(CORNER)
            
            if self.is_moving:
                self.frame_counter += 1
                if self.frame_counter == FPS_ratio:
                    self.animation_frame += 1
                    self.frame_counter = 0
            else:
                self.frame_counter = 0
                self.animation_frame = 0
            
            image_source_x = (self.animation_frame % self.num_animation_frames) * self.frame_width
            
            pushMatrix()
            translate(self.x_pos + self.screen_width//2, self.y_pos + self.screen_height//2)
            rotate(radians(self.rotation))
            copy(self.image, image_source_x, 0, self.frame_width, self.image_height, 0 - self.screen_width//2, 0 - self.screen_height//2, self.screen_width, self.screen_height)
            popMatrix()
            
            ## this is just a hitbox visual
            #noFill()
            #stroke(255,0,0)
            #rect(self.x_pos + self.screen_width*0.2, self.y_pos + self.screen_height*0.2, self.screen_width*0.6, self.screen_height*0.6)
            
        def movement(self):
            rotation_list = []
            
            self.x_velocity = self.y_velocity = 0
            
            if self.name != "Computer":
                for move_key in move_key_states:
                    if move_key_states[move_key] == True:
                        if move_key == self.controls[0]:
                            self.y_velocity -= self.speed
                            rotation_list.append(0)
                        elif move_key == self.controls[1]:
                            self.x_velocity -= self.speed
                            rotation_list.append(270)
                        elif move_key == self.controls[2]:
                            self.y_velocity += self.speed
                            rotation_list.append(180)
                        elif move_key == self.controls[3]:
                            self.x_velocity += self.speed
                            rotation_list.append(90)
            
            else:
                self.maze_pos = round((self.y_pos) / maze.cell_size, 1) , round((self.x_pos) / maze.cell_size, 1)
        
                if len(shortest_path) > 1:
                    if shortest_path[self.path_index+1] == self.maze_pos and self.path_index < len(shortest_path)-2:
                        self.path_index += 1
                
                    if shortest_path[self.path_index+1][1] > self.maze_pos[1]:
                        self.x_velocity += self.speed
                        rotation_list.append(90)
                    elif shortest_path[self.path_index+1][1] < self.maze_pos[1]:
                        self.x_velocity -= self.speed
                        rotation_list.append(270)    
                    elif shortest_path[self.path_index+1][0] > self.maze_pos[0]:
                        self.y_velocity += self.speed
                        rotation_list.append(180)  
                    elif shortest_path[self.path_index+1][0] < self.maze_pos[0]:
                        self.y_velocity -= self.speed
                        rotation_list.append(0)
                        
            self.x_pos += self.x_velocity
            self.collisions("x")
            
            self.y_pos += self.y_velocity
            self.collisions("y")
            
            if self.x_velocity == self.y_velocity == 0:
                self.is_moving = False
            else:
                self.is_moving = True
            
            
            if self.is_moving:
                self.rotation = get_circular_mean(rotation_list, True)
        
            
        def collisions(self, direction):
            boundaries = maze.screen_wall_positions
            for door in maze.door_info:
                if door[1] == "closed":
                    boundaries += door[0],
            
            for wall_pos in boundaries:
                if wall_pos[0]-maze.cell_size*0.8 < self.x_pos < wall_pos[0]+maze.cell_size*0.8 and wall_pos[1]-maze.cell_size*0.8 < self.y_pos < wall_pos[1]+maze.cell_size*0.8: 
                    
                    if direction == "x":
                        if self.x_velocity < 0 and not(wall_pos[0]-maze.cell_size*0.8 < self.x_pos-self.x_velocity < wall_pos[0]+maze.cell_size*0.8 and wall_pos[1]-maze.cell_size*0.8 < self.y_pos < wall_pos[1]+maze.cell_size*0.8):
                            ## deals with a special case in which you move up left or down left and get stuck when colliding with two walls at once
                            #if (wall_pos[0]+maze.cell_size, wall_pos[1]) in boundaries:
                                #pass
                            #else:
                            self.x_pos = wall_pos[0] + maze.cell_size*0.8
                            
                        elif self.x_velocity > 0 and not(wall_pos[0]-maze.cell_size*0.8 < self.x_pos-self.x_velocity < wall_pos[0]+maze.cell_size*0.8 and wall_pos[1]-maze.cell_size*0.8 < self.y_pos < wall_pos[1]+maze.cell_size*0.8):
                            self.x_pos = wall_pos[0] - maze.cell_size*0.8
                    
                    elif direction == "y":
                        if self.y_velocity < 0 and not(wall_pos[0]-maze.cell_size*0.8 < self.x_pos < wall_pos[0]+maze.cell_size*0.8 and wall_pos[1]-maze.cell_size*0.8 < self.y_pos-self.y_velocity < wall_pos[1]+maze.cell_size*0.8):
                            self.y_pos = wall_pos[1] + maze.cell_size*0.8
                            
                        elif self.y_velocity > 0 and not(wall_pos[0]-maze.cell_size*0.8 < self.x_pos < wall_pos[0]+maze.cell_size*0.8 and wall_pos[1]-maze.cell_size*0.8 < self.y_pos-self.y_velocity < wall_pos[1]+maze.cell_size*0.8):
                            self.y_pos = wall_pos[1] - maze.cell_size*0.8
            
            
            
            if direction == "y":
                if self.x_pos < 0:
                    self.x_pos = 0
                elif self.x_pos > 650*SF - maze.cell_size:
                    self.x_pos = 650*SF - maze.cell_size
                if self.y_pos < 0:
                    self.y_pos = 0
                elif self.y_pos > 500*SF - maze.cell_size:
                    self.y_pos = 500*SF - maze.cell_size
                
                if maze.screen_ending_pos[0]-maze.cell_size*0.8 < self.x_pos < maze.screen_ending_pos[0]+maze.cell_size*0.8 and maze.screen_ending_pos[1]-maze.cell_size*0.8 < self.y_pos < maze.screen_ending_pos[1]+maze.cell_size*0.8:
                    global winner
                    if self.finished_maze == False:
                        self.finished_maze = True
                        self.finish_time = game_time
                        self.score = int((maze.num_cols * maze.num_rows) / game_time)
                        if winner == None:
                            winner = self.name
                            self.win_count += 1
                        

def mousePressed():
    global mouse_clicked
    mouse_clicked = True

def mouseWheel(event):
    global mouse_scrolled
    mouse_scrolled = event.getCount()

def keyPressed():
    global key_pressed
    key_pressed = True
    
    for move_key in move_key_states:
        if key != CODED and key.upper() == move_key:
            move_key_states[key.upper()] = True
        elif keyCode == move_key:
            move_key_states[keyCode] = True
    
def keyReleased():
    for move_key in move_key_states:
        if key != CODED and key.upper() == move_key:
            move_key_states[key.upper()] = False
        elif keyCode == move_key:
            move_key_states[keyCode] = False 

def draw():
    global mouse_clicked, mouse_scrolled, key_pressed
    
    if mode == "selection":
        menu_screen()
    elif mode == "get name":
        get_name_screen()
    elif mode == "play":
        play_screen()
    elif mode == "help":
        help_screen()
    elif mode == "leaderboards":
        leaderboards_screen()
    
    display_taskbar()
    
    if mouse_clicked == True: ## mouse_clicked only returns true if the mouse was clicked on that frame
        mouse_clicked = False
    if mouse_scrolled != 0: ## mouse_scrolled only returns 1 or -1 if the mouse is scrolled on that frame
        mouse_scrolled = 0
    if key_pressed == True: ## key_pressed only returns true if a key was pressed on that frame
        key_pressed = False               

## sets up all player information depending on which game mode was selected
def setup_players():
    Player.player_list = []
    
    player1 = Player(all_anim_info["player1"][0], all_anim_info["player1"][1], all_anim_info["player1"][2], all_anim_info["player1"][3], move_key_order["player1"])
    
    if game_mode == "player vs player":
        player2 = Player(all_anim_info["player2"][0], all_anim_info["player2"][1], all_anim_info["player2"][2], all_anim_info["player2"][3], move_key_order["player2"])
    
    elif game_mode == "player vs computer":
        global AI
        AI = Player(all_anim_info["AI"][0], all_anim_info["AI"][1], all_anim_info["AI"][2], all_anim_info["AI"][3], None)
        AI.name = "Computer"

## sets up all the data to start a new maze
def setup_maze():
    global maze, game_time, frame_counter, winner
    
    num_cols = random.randint(maze_info["min_num_cols"], maze_info["max_num_cols"]) //2*2+1
    num_rows = random.randint(maze_info["min_num_rows"], maze_info["max_num_rows"]) //2*2+1
    
    maze = Maze(num_cols, num_rows, maze_info["num_doors"], maze_info["door_flip_frequency"])
    maze.generate_maze()
    maze.make_start_end_points()
    maze.make_doors()
    if game_mode == "player vs computer":
        maze.find_path(maze.starting_pos)
        AI.path_index = 0
        
    maze.calc_cell_size()
    maze.screen_wall_positions = maze.calc_cell_positions("w")
    maze.screen_door_positions = maze.calc_cell_positions("d")
    maze.create_door_info()
    maze.screen_starting_pos = maze.starting_pos[1]*maze.cell_size, maze.starting_pos[0]*maze.cell_size
    maze.screen_ending_pos = maze.ending_pos[1]*maze.cell_size, maze.ending_pos[0]*maze.cell_size
    
    for player in Player.player_list:
        player.x_pos = maze.screen_starting_pos[0]
        player.y_pos = maze.screen_starting_pos[1]
        player.screen_width = player.screen_height = maze.cell_size
        player.speed = maze.cell_size * 0.06
        player.finished_maze = False
        player.score_saved = False
    
    game_time = -3.5
    frame_counter = 0
    winner = None

## handles all the functions that need to be called during a game
def play_screen():
    global frame_counter, game_time
    
    background(200)
    
    maze.flip_doors()
    maze.display()
    
    for player in Player.player_list:
        if game_time >= 0:
            player.movement()
        player.display()
    
    # time counter in seconds
    frame_counter += 1
    if frame_counter == FPS // 10:
        frame_counter = 0
        game_time = round(game_time + 0.1, 1)
    
    countdown()
    display_banner()
    
    if winner != None:
        winner_screen()

## handles the countdown at the start of a game before players are able to begin moving
def countdown():
    if game_time < 1:
        noStroke()
        fill(0, 100)
        rect(285*SF, 220*SF, 80*SF, 70*SF)
        fill(255)
        textSize(60*SF)
            
        if -3 < game_time < 0:
            text(str(int((game_time - 1) * -1)), 325*SF, 250*SF)
        elif game_time >= 0:
            text("Go", 325*SF, 250*SF)
            
    if game_time == -3.5 and frame_counter == 1:
        all_sound_info["countdown"].trigger()

## displays the banner that shows all the game information during a game        
def display_banner():
    global mode, game_status, highscores
    stroke(0)
    fill(255)
    rect(650*SF, -1, width+1, height+1) 
    fill(0)
    textSize(20*SF)
    text("Maze Type:", 725*SF, 20*SF)
    text(str(maze.num_cols) + "x" + str(maze.num_rows), 725*SF, 45*SF)
    if game_time >= 0:
        text("Time: " + digital_clock(game_time), 725*SF, 85*SF)
    else:
        text("Time: 0:00.0", 725*SF, 85*SF)
    
    for i, player in enumerate(Player.player_list):
        fill(0)
        textSize(20*SF)
        text(player.name + "'s", 725*SF, (135+150*i) * SF)
        text("Wins: " + str(player.win_count), 725*SF, (160+150*i) * SF)
        
        if player.finished_maze:
            text("Time: " + digital_clock(player.finish_time), 725*SF, (185+150*i) * SF)
            
            text("Score: " + str(player.score), 725*SF, (210+150*i) * SF)
            
            if player.name != "Computer":
                if player.score_saved == False:
                    if 675*SF < mouseX < 775*SF and (230+150*i)*SF < mouseY < (245+150*i)*SF:
                        textSize(25*SF)
                        if mouse_clicked:
                            best_score = save_score("highscores.txt", [player.score, player.name, str(maze.num_cols) + "x" + str(maze.num_rows), player.finish_time])
                            if best_score == True:
                                highscores = pickle_read("highscores.txt")
                                player.score_saved = True
                            elif best_score == False:
                                player.score_saved = "not best score"
                    else:
                        textSize(20*SF)
                    fill(255,0,225)
                    text("Save Score", 725*SF, (235+150*i) * SF)
                
                elif player.score_saved == True:
                    fill(153,50,255)
                    text("Score Saved", 725*SF, (235+150*i) * SF)
                
                else:
                    fill(255,0,0)
                    text("Not Best Score", 725*SF, (235+150*i) * SF)

            
    if 680*SF < mouseX < 770*SF and 465*SF < mouseY < 480*SF:
        textSize(25*SF)
        if mouse_clicked:
            mode = "selection"
            game_status = False
            reset_variables()
    else:
        textSize(20*SF)
    fill(0)
    text("End Game", 725*SF, 470*SF)

## takes in a time in seconds, outputs a string of the time in a digital clock's format
def digital_clock(time):
    return str(int(time)//600) + str(int(time)//60%10) + ":" + str(int(time)//10%6) + str(time%10)

## displays who won and the option to play again
def winner_screen():
    global mode
    
    fill(0,125)
    noStroke()
    rect(145*SF, 225*SF, 380*SF, 60*SF)
    fill(255)
    textSize(40*SF)
    text(winner + " Won!", 325*SF, 250*SF)
    
    fill(0)
    if 675*SF < mouseX < 775*SF and 425*SF < mouseY < 440*SF:
        textSize(25*SF)
        if mouse_clicked:
            setup_maze()
            mode = "play"
    else:
        textSize(20*SF)
    text("Play Again", 725*SF, 430*SF)
    
## takes in a file name, outputs a 2d list with the items of the file
def read_file(file_name):
    try:
        f = open(file_name)
    except IOError:
        file_create = open(file_name, "w")
        file_create.close()
        f = open(file_name)
    
    file_data = []    

    for line in f.readlines():
        line = line.strip()
        line = line.split(",")
        
        ## converts any items into integers if they can convert
        for i in range(len(line)):
            try:
                line[i] = int(line[i])
            except ValueError:
                pass
                
        file_data.append(line)
    f.close()
    return(file_data)

## takes in a list of angles, gets the circular mean
def get_circular_mean(angle_list, degrees):
    num_angles = len(angle_list)
    
    if degrees == True:
        for i in range(num_angles):
            angle_list[i] *= math.pi/180

    vector_x_list = []
    vector_y_list = []
    for angle in angle_list:
        vector_x = math.cos(angle)
        vector_y = math.sin(angle)
        vector_x_list.append(vector_x)
        vector_y_list.append(vector_y)

    average_vector = sum(vector_x_list)/num_angles, sum(vector_y_list)/num_angles
    
    average_angle = math.atan2(average_vector[1],average_vector[0])
    
    if degrees == True:
        average_angle *= 180/math.pi

    return average_angle

## displays a selection of the different screens the player can choose to switch to
def display_taskbar():
    global mode
    
    fill(255)
    stroke(0)
    rect(-1,500*SF,width+2,600*SF)
    fill(0)
    textAlign(CENTER,CENTER)
    if 70*SF < mouseX < 130*SF and 540*SF < mouseY < 570*SF:
        textSize(40*SF)
        if mouse_clicked:
            reset_variables()
            mode = "selection"
    else:
        textSize(30*SF)
    text("Menu", 100*SF, 550*SF)
    
    if 270*SF < mouseX < 330*SF and 540*SF < mouseY < 570*SF:
        textSize(40*SF)
        if mouse_clicked:
            reset_variables()
            mode = "help"
    else:
        textSize(30*SF)
    text("Help", 300*SF, 550*SF)
    
    if 470*SF < mouseX < 530*SF and 540*SF < mouseY < 570*SF:
        textSize(40*SF)
        if mouse_clicked:
            reset_variables()
            mode = "leaderboards"
    else:
        textSize(30*SF)
    text("Scores", 500*SF, 550*SF) 

    if 670*SF < mouseX < 730*SF and 540*SF < mouseY < 570*SF:
        textSize(40*SF)
        if mouse_clicked:
            exit()
    else:
        textSize(30*SF)        
    text("Exit", 700*SF, 550*SF) 

## displays a screen where plays select their game mode
def menu_screen():
    global mode, game_mode, game_status
    
    background(153,50,255)
    imageMode(CENTER)
    image(all_image_info["title"], width*0.5, 100*SF, 400*SF, 160*SF)
    
    noStroke()
    fill(255)
    textAlign(CENTER,CENTER)
    
    if 280*SF < mouseX < 520*SF and 200*SF < mouseY < 230*SF:
        textSize(50*SF)
        if mouse_clicked:
            mode = "get name"
            game_mode = "singleplayer"
            game_status = False
            setup_players()
            setup_maze()
    else:
        textSize(40*SF)
    text("Singleplayer", 400*SF, 210*SF)
    
    if 250*SF < mouseX < 550*SF and 270*SF < mouseY < 300*SF:
        textSize(50*SF)
        if mouse_clicked:
            mode = "get name"
            game_mode = "player vs player"
            game_status = False
            setup_players()
            setup_maze()
    else:
        textSize(40*SF)
    text("Player vs Player", 400*SF, 280*SF)
    
    if 215*SF < mouseX < 590*SF and 340*SF < mouseY < 370*SF:
        textSize(50*SF)
        if mouse_clicked:
            mode = "get name"
            game_mode = "player vs computer"
            game_status = False
            setup_players()
            setup_maze()
    else:
        textSize(40*SF)
    text("Player vs Computer", 400*SF, 350*SF)
    
    textSize(40*SF)
    if game_status == False:
        fill(170)
    else:
        if 250*SF < mouseX < 550*SF and 410*SF < mouseY < 440*SF:
            textSize(50*SF)
            if mouse_clicked:
                mode = "play"
    text("Continue Game", 400*SF, 420*SF)

## gets the player(s) to type in their name before playing
def get_name_screen():
    global player_name, mode, game_status
    
    background(153,50,255)
    imageMode(CENTER)
    image(all_image_info["title"], width*0.5, 100*SF, 400*SF, 160*SF)
    fill(255)
    textAlign(CENTER,CENTER)
    
    if key_pressed:
        if key != CODED and key in "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz" and len(player_name) < max_name_length:
            player_name += key.upper()
        elif key == BACKSPACE:
            player_name = player_name[0:len(player_name)-1]
    
    if game_mode == "player vs player":
        two_names = True
        if Player.player_list[0].name == None:
            first_name = True
        else: 
            first_name = False
    else:
        two_names = False
    
    textSize(40*SF)
    if two_names == True and first_name == False:
        fill(0,0,255)
        text("Player 2 Enter Name:", 400*SF, 210*SF)
    else:
        fill(255,0,0)
        text("Player 1 Enter Name:", 400*SF, 210*SF)
    fill(255)
    text(player_name, 400*SF, 280*SF)
    
    textSize(20*SF)
    text("Max Name Length = " + str(max_name_length), 400*SF, 350*SF)
    
    textSize(40*SF)
    if len(player_name) == 0:
        fill(170)
    else:
        if 350*SF < mouseX < 450*SF and 410*SF < mouseY < 440*SF:
            textSize(50*SF)
            if mouse_clicked:
                if two_names == False:
                    Player.player_list[0].name = player_name
                    mode = "play"
                    game_status = True
                elif first_name == True:
                    Player.player_list[0].name = player_name
                    player_name = ""
                else:
                    Player.player_list[1].name = player_name
                    mode = "play"
                    game_status = True
                
    text("Done", 400*SF, 420*SF)

## displays the help information
def help_screen():
    imageMode(CORNER)
    image(all_image_info["help"],0,0,width,500*SF)  

## displays the leaderboards
def leaderboards_screen():
    global leaderboards_scroll
    
    background(200)
    
    if (mouse_scrolled == 1 and leaderboards_scroll > (len(highscores)-6) * -54 * SF ) or (mouse_scrolled == -1 and leaderboards_scroll < 0):
        leaderboards_scroll += mouse_scrolled * -27
        
    textSize(25*SF)
    fill(255,0,255)
    for rank, score in enumerate(highscores[::-1]):
        textAlign(LEFT)
        text(str(rank+1) + ". " + score[1], 100*SF, (170+rank*54 + leaderboards_scroll)*SF)
        textAlign(CENTER)
        text(score[2], 350*SF, (170+rank*54 + leaderboards_scroll)*SF)
        text(digital_clock(score[3]), 500*SF, (170+rank*54 + leaderboards_scroll)*SF)
        textAlign(RIGHT)
        text(str(score[0]), 700*SF, (170+rank*54 + leaderboards_scroll)*SF)
    
    imageMode(CORNER)
    image(all_image_info["leaderboards"],0,0,width,500*SF)

## takes in a pickle file name, outputs the file's data                    
def pickle_read(file_name):
    with open( file_name, 'rb') as f:
        file_data = pickle.load(f)
    f.close()
    return(file_data)

## takes in a file name and data, pickle writes the data to that file
def pickle_write(file_name, write_data):
    with open( file_name, 'wb') as f:
        pickle.dump(write_data, f)
    f.close()

## takes in a list, then sorts the list
def insertion_sort(the_list):
    for i in range(len(the_list)-1):
        min_val_index = i
        for j in range(1+i, len(the_list)):
            if the_list[min_val_index] > the_list[j]:
                min_val_index = j
        the_list.insert(i, the_list.pop(min_val_index))

## takes in a list, outputs a list with the sorted order of the list
def indirect_sort(the_list):
    indirect_list = [i for i in range(len(the_list))]

    for i in range(len(the_list)-1):
        min_val_index = i
        for j in range(1+i, len(the_list)):
            if the_list[indirect_list[min_val_index]] > the_list[indirect_list[j]]:
                min_val_index = j
        indirect_list[i], indirect_list[min_val_index] = indirect_list[min_val_index], indirect_list[i]
    
    return indirect_list

## takes in a sorted list of items and a search item, then outputs the index of the search item in the list, or -1 if it isn't in it
def binary_search(sorted_list, search_item):
    bottom = 0
    top = len(sorted_list) - 1
    middle = 0
 
    while bottom <= top:
        middle = (top + bottom) // 2
 
        if sorted_list[middle] < search_item:
            bottom = middle + 1
 
        elif sorted_list[middle] > search_item:
            top = middle - 1
 
        else:
            return middle
 
    return -1
        
## takes in the file name and player score info, if it is their best score, overwrites the score to the file and returns True, if it is not their best score, returns False
def save_score(file_name, player_score):   
    ## finds previous score of the same player name
    indirect_list = indirect_sort([score[1] for score in highscores])
    sorted_name_list = [highscores[i][1] for i in indirect_list]
    indirect_index = binary_search(sorted_name_list, player_score[1])
    if indirect_index != -1:
        search_index = indirect_list[indirect_index]
        
        ## checks if previous score is better than current score
        if player_score[0] <= highscores[search_index][0]:
            return(False)
        else:
            del highscores[search_index]
    
    highscores.append(player_score)
    insertion_sort(highscores)
    pickle_write(file_name, highscores)
    return(True)
