from board import Board, LAVA_EFFECT
from pieces import Piece
from utils import algebraic_to_coords, coords_to_algebraic
import copy
import random
import abilities as abilities_module

class Game:
    PIECE_SP_VALUES = {"PAWN": 1, "KNIGHT": 3, "BISHOP": 3, "ROOK": 5, "QUEEN": 9, "KING": 0}
    CENTRAL_ZONES = [(3,3), (3,4), (4,3), (4,4)]
    SP_PER_CENTRAL_ZONE = 1
    QUICK_DECISION_SP_BONUS = 1

    def __init__(self, ai_player_color='black'):
        self.abilities_module = abilities_module
        self.board = Board(self)
        self.current_player = "white"
        self.ai_player_color = ai_player_color
        self.game_over = False; self.winner = None
        self.utils = {'algebraic_to_coords': algebraic_to_coords, 'coords_to_algebraic': coords_to_algebraic}
        self.full_turn_counter = 0
        self.player_sp = {'white': 0, 'black': 0}
        self.player_lost_pieces = {'white': [], 'black': []}
        self.SPECIAL_MOVES = {
            'redeploy': {
                'name': 'Redeploy Captured Piece', 'sp_cost': 10, 'effect': self._redeploy_captured_piece_effect,
                'requires_target': True, 'target_prompt': "Piece type and target square (e.g. Pawn e1):"
            },
            'freeze_pawns': {
                'name': 'Global Freeze Pawns', 'sp_cost': 15, 'effect': self._global_freeze_pawns_effect,
                'requires_target': False, 'target_prompt': ""
            }
        }
        self._start_turn_prep()

    def _start_turn_prep(self): # (Unchanged)
        self.board.update_visibility(self.current_player)
        self.check_zone_control_sp(self.current_player)
        for piece in self.board.get_all_pieces():
            if piece.color == self.current_player and 'frozen' in piece.status_effects:
                piece.status_effects['frozen'] -= 1
                if piece.status_effects['frozen'] <= 0:
                    del piece.status_effects['frozen']
                    print(f"{piece} @ {self.utils['coords_to_algebraic'](piece.position)} unfrozen.")

    def _post_action_cleanup(self): self.switch_player() # (Unchanged)

    def switch_player(self): # (Unchanged)
        self.current_player = "black" if self.current_player == "white" else "white"
        if self.current_player == "white":
            self.full_turn_counter += 1; self.board.board_evolution_timer +=1
            if self.board.board_evolution_timer >= self.board.turns_before_evolution:
                self.board.generate_tile_effects(self)
        self._start_turn_prep()

    def add_sp(self, player, amount): # (Unchanged)
        if amount > 0: self.player_sp[player] += amount; print(f"{player.capitalize()} +{amount} SP! Total: {self.player_sp[player]}.")
        elif amount < 0: self.player_sp[player] = max(0, self.player_sp[player] + amount)

    def add_lost_piece(self, owner, type_name_upper): self.player_lost_pieces[owner].append(type_name_upper) # (Unchanged)
    def check_zone_control_sp(self, player): # (Unchanged)
        gain = sum(self.SP_PER_CENTRAL_ZONE for r,c in self.CENTRAL_ZONES if self.board.get_piece((r,c)) and self.board.get_piece((r,c)).color == player)
        if gain > 0: self.add_sp(player, gain)

    def _is_move_putting_king_in_check(self, player_color, start_coords, end_coords): # (Unchanged)
        hypo_board = copy.deepcopy(self.board)
        original_piece = self.board.get_piece(start_coords)
        if not original_piece : return True
        hypo_piece = hypo_board.get_piece(start_coords)
        if hypo_piece: hypo_piece.has_speed_buff = original_piece.has_speed_buff
        hypo_board.move_piece(start_coords, end_coords, self)
        return self.is_in_check(player_color, hypo_board)

    def _redeploy_captured_piece_effect(self, player, args): # (Unchanged)
        if len(args)<2: print("Redeploy: Need type & target sq."); return False
        type_str, sq_str = args[0], args[1]; coords = self.utils['algebraic_to_coords'](sq_str)
        if not coords: print(f"Redeploy: Invalid target {sq_str}."); return False
        r,c=coords
        if self.board.get_piece(coords): print(f"Redeploy: Target {sq_str} occupied."); return False
        if self.board.tile_effects[r][c] == self.board.LAVA_EFFECT: print(f"Redeploy: Target {sq_str} is LAVA."); return False
        valid_row = 7 if player=='white' else 0 # White redeploys on row 7 (rank 1), Black on row 0 (rank 8)
        if r!=valid_row: print(f"Redeploy: Not on back rank for {player}. Target row {r}, expected {valid_row}"); return False
        type_upper = type_str.upper()
        if type_upper in self.player_lost_pieces[player]:
            new_p = self.board.create_piece_by_str_and_color(type_upper, player, coords)
            if new_p:
                self.board.grid[r][c]=new_p; new_p.assign_ability()
                self.player_lost_pieces[player].remove(type_upper)
                print(f"{player.capitalize()} redeployed {type_upper} to {sq_str}!"); self.board.update_visibility(player)
                return True
        print(f"Redeploy: No captured '{type_upper}' for {player}. Lost: {self.player_lost_pieces[player]}"); return False


    def _global_freeze_pawns_effect(self, player, args=None): # (Unchanged)
        print(f"{player.capitalize()} activates Global Freeze Pawns!"); frozen=False
        for p in self.board.get_all_pieces():
            if p.piece_type_name=="PAWN": p.status_effects['frozen']=1; frozen=True; print(f"{p.color} Pawn @ {self.utils['coords_to_algebraic'](p.position)} frozen!")
        if not frozen: print("No pawns to freeze.");
        return True

    def handle_special_move(self, player, key, args_list=None): # (Unchanged)
        if args_list is None: args_list=[]
        move=self.SPECIAL_MOVES.get(key)
        if not move: print(f"Unknown special: {key}"); return False
        if self.player_sp[player] < move['sp_cost']: print(f"Not enough SP for {move['name']}."); return False
        # print(f"{player.capitalize()} attempts Special: {move['name']}...") # Moved to AI specific message
        if move['effect'](player, args_list):
            self.player_sp[player]-=move['sp_cost']; print(f"{move['name']} successful! Cost {move['sp_cost']}.")
            self.add_sp(player, self.QUICK_DECISION_SP_BONUS); self._post_action_cleanup(); return True
        else: print(f"{move['name']} failed."); return False

    def play_turn(self, start_str, end_str): # (Unchanged)
        start_coords, end_coords = self.utils['algebraic_to_coords'](start_str), self.utils['algebraic_to_coords'](end_str)
        if not start_coords or not end_coords: print("Invalid coords."); return False
        if start_coords==end_coords: print("Same start/end."); return False
        if self.board.tile_effects[end_coords[0]][end_coords[1]]==self.board.LAVA_EFFECT: print("Dest is LAVA."); return False
        p=self.board.get_piece(start_coords)
        if not p: print(f"No piece @ {start_str}."); return False
        if p.color!=self.current_player: print("Not your piece."); return False
        if not p.is_action_allowed(): print(f"{p} is frozen!"); return False
        if not p.is_valid_move(self.board,start_coords,end_coords) or self._is_move_putting_king_in_check(self.current_player,start_coords,end_coords):
            # print(f"Invalid move for {p} {start_str}->{end_str}."); # AI will print its own, human gets this
            if self.current_player != self.ai_player_color: print(f"Invalid move for {p} {start_str}->{end_str}.")
            return False
        cap=self.board.move_piece(start_coords,end_coords,self)
        # Message printing moved to AI handler for AI moves
        if self.current_player != self.ai_player_color:
            if cap: print(f"{p} captures {cap}.")
            else: print(f"{p} moves {start_str}->{end_str}.")
        self.add_sp(self.current_player,self.QUICK_DECISION_SP_BONUS); self._post_action_cleanup(); return True

    def handle_ability_activation(self, piece_str, target_str=None): # (Unchanged)
        pc_coords=self.utils['algebraic_to_coords'](piece_str)
        if not pc_coords: print("Invalid piece_pos"); return False
        p=self.board.get_piece(pc_coords)
        if not p: print("No piece"); return False
        if p.color!=self.current_player: print("Not your piece"); return False
        if not p.is_action_allowed(): print(f"{p} is frozen!"); return False
        if not p.ability: print("No ability"); return False
        if p.ability_cooldown>0: print("Ability on CD"); return False
        tgt_coords=None
        if p.ability.target_type!='self':
            if not target_str and ('square' in p.ability.target_type or 'piece' in p.ability.target_type): print("Needs target"); return False
            if target_str:
                tgt_coords=self.utils['algebraic_to_coords'](target_str)
                if not tgt_coords: print("Invalid target_pos"); return False
                if self.board.tile_effects[tgt_coords[0]][tgt_coords[1]]==self.board.LAVA_EFFECT: print("Target LAVA"); return False
        hypo_b=copy.deepcopy(self.board); hypo_p=hypo_b.get_piece(pc_coords); hypo_g=copy.copy(self); hypo_g.board=hypo_b
        # Make sure hypothetical piece has correct ability reference for effect_logic
        if hypo_p: hypo_p.ability = p.ability

        if p.ability.effect_logic(hypo_g,hypo_p,tgt_coords):
            if self.is_in_check(self.current_player,hypo_b): print("Ability puts King in check."); return False
        else: return False
        if p.ability.effect_logic(self,p,tgt_coords):
            # Message printing moved to AI handler for AI
            if self.current_player != self.ai_player_color: print(f"{p} used {p.ability.name}.")
            p.ability_cooldown=p.ability.cooldown_max
            self.add_sp(self.current_player,self.QUICK_DECISION_SP_BONUS); self._post_action_cleanup(); return True
        return False

    def _generate_ai_ability_uses(self, ai_pieces): # (Unchanged from previous step)
        possible_ability_uses = []
        for piece in ai_pieces:
            if piece.ability and piece.ability_cooldown == 0 and piece.is_action_allowed():
                ability_name = piece.ability.name
                target_type = piece.ability.target_type
                potential_targets = []
                if target_type == 'empty_square':
                    for _ in range(5):
                        range_limit = piece.ability.range_limit if hasattr(piece.ability, 'range_limit') else 2
                        rand_r_offset = random.randint(-range_limit, range_limit)
                        rand_c_offset = random.randint(-range_limit, range_limit)
                        tr, tc = piece.position[0] + rand_r_offset, piece.position[1] + rand_c_offset
                        if self.board._is_on_board(tr, tc) and self.board.get_piece((tr,tc)) is None and \
                           self.board.tile_effects[tr][tc] != self.board.LAVA_EFFECT:
                            potential_targets.append((tr,tc))
                elif target_type == 'ally_piece_adjacent':
                    for dr in [-1,0,1]:
                        for dc in [-1,0,1]:
                            if dr==0 and dc==0: continue
                            tr, tc = piece.position[0]+dr, piece.position[1]+dc
                            if self.board._is_on_board(tr,tc):
                                target_piece = self.board.get_piece((tr,tc))
                                if target_piece and target_piece.color == self.ai_player_color and target_piece != piece:
                                    potential_targets.append((tr,tc))
                elif target_type == 'self': potential_targets.append(None)
                for target_coords in potential_targets:
                    hypo_b_abil = copy.deepcopy(self.board); hypo_p_abil = hypo_b_abil.get_piece(piece.position)
                    if hypo_p_abil: hypo_p_abil.ability = piece.ability # Ensure correct ability ref for hypo piece
                    hypo_g_abil = copy.copy(self); hypo_g_abil.board = hypo_b_abil
                    if piece.ability.effect_logic(hypo_g_abil, hypo_p_abil, target_coords):
                        if not self.is_in_check(self.ai_player_color, hypo_b_abil):
                            possible_ability_uses.append({'type': 'ability', 'piece_pos': piece.position,
                                                          'target_pos': target_coords, 'ability_name': ability_name,
                                                          'piece_repr': str(piece)})
                    if len(possible_ability_uses) > 5 and target_type != 'self': break
            if len(possible_ability_uses) > 10 : break
        return possible_ability_uses

    def _generate_ai_special_moves(self, player_color):
        possible_special_moves = []
        available_sp = self.player_sp[player_color]

        for key, move_data in self.SPECIAL_MOVES.items():
            if available_sp >= move_data['sp_cost']:
                if key == 'redeploy':
                    if self.player_lost_pieces[player_color]:
                        lost_piece_type = random.choice(self.player_lost_pieces[player_color])
                        redeploy_row = 0 if player_color == 'black' else 7
                        # Try a few random columns for redeployment
                        possible_cols = list(range(8))
                        random.shuffle(possible_cols)
                        for col in possible_cols[:3]: # Try up to 3 random columns
                            target_coords = (redeploy_row, col)
                            target_sq_str = self.utils['coords_to_algebraic'](target_coords)
                            # Validate target square (must be empty, not lava)
                            if self.board.get_piece(target_coords) is None and \
                               self.board.tile_effects[target_coords[0]][target_coords[1]] != self.board.LAVA_EFFECT:
                                # Redeploy doesn't cause self-check in a direct way
                                possible_special_moves.append({'type': 'special', 'key': key,
                                                               'args': [lost_piece_type, target_sq_str],
                                                               'name': move_data['name']})
                                break # Found a valid spot for this piece type
                elif key == 'freeze_pawns':
                    # No target, no complex validation beyond SP cost
                    # Effect does not alter board state to cause self-check
                    possible_special_moves.append({'type': 'special', 'key': key, 'args': [],
                                                   'name': move_data['name']})
        return possible_special_moves

    def handle_ai_turn(self): # (Now includes special moves)
        print(f"\n--- {self.ai_player_color.capitalize()}'s Turn (AI) ---")
        if self.current_player != self.ai_player_color: return

        ai_pieces = [p for p in self.board.get_all_pieces() if p.color == self.ai_player_color and p.is_action_allowed()]
        possible_std_moves = []
        for piece in ai_pieces: # (Standard move generation unchanged)
            start_pos = piece.position
            for r_idx in range(8):
                for c_idx in range(8):
                    end_pos = (r_idx, c_idx)
                    if start_pos == end_pos or self.board.tile_effects[r_idx][c_idx] == self.board.LAVA_EFFECT: continue
                    if piece.is_valid_move(self.board, start_pos, end_pos) and \
                       not self._is_move_putting_king_in_check(self.ai_player_color, start_pos, end_pos):
                        possible_std_moves.append({'type': 'move', 'start_pos': start_pos, 'end_pos': end_pos,
                                                   'piece_repr': str(piece)})

        possible_ability_uses = self._generate_ai_ability_uses(ai_pieces)
        possible_special_moves = self._generate_ai_special_moves(self.ai_player_color)

        all_possible_actions = possible_std_moves + possible_ability_uses + possible_special_moves
        if not all_possible_actions:
            print(f"AI ({self.ai_player_color}) has no valid actions. Passing."); self._post_action_cleanup(); return

        selected_action = random.choice(all_possible_actions)
        action_type = selected_action['type']
        print(f"AI ({self.ai_player_color}) is thinking...")

        if action_type == 'move':
            start_sq_str = self.utils['coords_to_algebraic'](selected_action['start_pos'])
            end_sq_str = self.utils['coords_to_algebraic'](selected_action['end_pos'])
            print(f"AI MOVE: {selected_action['piece_repr']} from {start_sq_str} to {end_sq_str}.")
            self.play_turn(start_sq_str, end_sq_str)
        elif action_type == 'ability':
            piece_pos_str = self.utils['coords_to_algebraic'](selected_action['piece_pos'])
            target_pos_str = self.utils['coords_to_algebraic'](selected_action['target_pos']) if selected_action['target_pos'] else None
            print(f"AI ABILITY: {selected_action['ability_name']} by {selected_action['piece_repr']} "
                  f"{('targeting ' + target_pos_str) if target_pos_str else ''}.")
            self.handle_ability_activation(piece_pos_str, target_pos_str)
        elif action_type == 'special':
            key = selected_action['key']
            args = selected_action.get('args', [])
            print(f"AI SPECIAL: {selected_action['name']} with args {args}.")
            self.handle_special_move(self.ai_player_color, key, args)
        else: print("AI chose unknown action. Passing."); self._post_action_cleanup()

    def _find_king_position(self, player, board_state): # (Unchanged)
        for r,row_data in enumerate(board_state.grid):
            for c,p_obj in enumerate(row_data):
                if p_obj and p_obj.piece_type_name=="KING" and p_obj.color==player: return (r,c)
        return None
    def is_in_check(self, player, board_state): # (Unchanged)
        king_pos=self._find_king_position(player,board_state)
        if not king_pos: return True
        opp= "black" if player=="white" else "white"
        # Iterate over a copy of the grid for safety if board_state can change during iteration
        grid_to_check = board_state.grid
        for r,row_data in enumerate(grid_to_check):
            for c,p_obj in enumerate(row_data): # p_obj is from board_state
                if p_obj and p_obj.color==opp:
                    # Pass board_state to is_valid_move
                    if p_obj.is_valid_move(board_state,(r,c),king_pos): return True
        return False

if __name__ == "__main__": # (Main loop unchanged)
    game = Game(ai_player_color='black')
    while not game.game_over:
        game.board.display(game)
        print(f"Player: {game.current_player} (SP: {game.player_sp[game.current_player]}) | Lost: W{game.player_lost_pieces['white']} B{game.player_lost_pieces['black']} | Turn: {game.full_turn_counter+1}")
        if game.is_in_check(game.current_player, game.board): print(f"{game.current_player.upper()} IS IN CHECK!")
        if game.current_player == game.ai_player_color and not game.game_over: game.handle_ai_turn()
        else:
            action = input("Action ('move S E', 'ability P [T]', 'special M [ARGS...]', 'togglefog', 'quit'): ").lower().split()
            if not action: continue; cmd=action[0]
            if cmd=='quit': break
            elif cmd=='togglefog': game.board.fog_of_war_on = not game.board.fog_of_war_on; game.board.update_visibility(game.current_player); print(f"FoW {'ON' if game.board.fog_of_war_on else 'OFF'}.")
            elif cmd=='move':
                if len(action)==3: game.play_turn(action[1],action[2])
                else: print("Format: move S E")
            elif cmd=='ability':
                if len(action)>=2: game.handle_ability_activation(action[1],action[2] if len(action)==3 else None)
                else: print("Format: ability P [T]")
            elif cmd=='special':
                if len(action)>=2: game.handle_special_move(game.current_player,action[1],action[2:] if len(action)>2 else [])
                else: print("Format: special M [params...]")
            else: print(f"Unknown: {cmd}.")
    print("\nGame finished.")
