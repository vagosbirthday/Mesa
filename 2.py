import mesa
import random
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
# Clases de agentes
class Box(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Pallet(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.stack_count = 0

class RobotAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying_box = False
        self.movements = 0

    def sense_environment(self):
        cell_content = self.model.grid.get_cell_list_contents([self.pos])
        is_box = any(isinstance(obj, Box) for obj in cell_content)
        is_pallet = any(isinstance(obj, Pallet) for obj in cell_content)
        return is_box, is_pallet

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)
        self.movements += 1

    def pick_box(self):
        if not self.carrying_box:
            cell_content = self.model.grid.get_cell_list_contents([self.pos])
            boxes = [obj for obj in cell_content if isinstance(obj, Box)]
            if boxes:
                self.carrying_box = True
                self.model.grid.remove_agent(boxes[0])

    def drop_box(self):
        if self.carrying_box:
            cell_content = self.model.grid.get_cell_list_contents([self.pos])
            pallets = [obj for obj in cell_content if isinstance(obj, Pallet)]
            if pallets:
                pallets[0].stack_count += 1
                self.carrying_box = False

    def step(self):
        is_box, is_pallet = self.sense_environment()
        if self.carrying_box:
            self.drop_box()
        elif is_box:
            self.pick_box()
        else:
            self.move()

# Modelo del almacén
class WarehouseModel(mesa.Model):
    def __init__(self, width, height, num_boxes, num_robots, num_pallets):
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.num_boxes = num_boxes

        for i in range(num_boxes):
            box = Box(i, self)
            self.schedule.add(box)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(box, (x, y))

        for i in range(num_pallets):
            pallet = Pallet(num_boxes + i, self)
            self.schedule.add(pallet)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(pallet, (x, y))

        for i in range(num_robots):
            robot = RobotAgent(num_boxes + num_pallets + i, self)
            self.schedule.add(robot)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(robot, (x, y))

    def step(self):
        self.schedule.step()

    def all_boxes_stacked(self):
        total_boxes = sum([pallet.stack_count for pallet in self.schedule.agents if isinstance(pallet, Pallet)])
        return total_boxes == self.num_boxes

def agent_portrayal(agent):
    if isinstance(agent, Box):
        return {"Shape": "rect", "Color": "blue", "Layer": 0, "w": 0.5, "h": 0.5}
    elif isinstance(agent, Pallet):
        return {"Shape": "rect", "Color": "green", "Layer": 0, "w": 0.5, "h": 0.5, "text": agent.stack_count, "text_color": "white"}
    elif isinstance(agent, RobotAgent):
        color = "red" if agent.carrying_box else "orange"
        return {"Shape": "circle", "Color": color, "Layer": 1, "r": 0.5}

# Parámetros del modelo
width, height = 10, 10
num_boxes = 20
num_robots = 5
num_pallets = 5

# Módulo de visualización
grid = CanvasGrid(agent_portrayal, width, height, 500, 500)
server = ModularServer(WarehouseModel, [grid], "Warehouse Simulation", {
    "width": width, "height": height, "num_boxes": num_boxes, "num_robots": num_robots, "num_pallets": num_pallets
})
server.port = 8521
server.launch()
