import mesa
import random
import matplotlib.pyplot as plt

# Clase Box
# Representa una caja en el almacén.
# Hereda de mesa.Agent.
# No tiene funcionalidad específica, pero sirve como entidad para interactuar con robots.
class Box(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

# Clase Pallet
# Representa un pallet donde las cajas pueden ser depositadas.
# Hereda de mesa.Agent.
# stack_count: Cuenta el número de cajas apiladas en el pallet.
class Pallet(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.stack_count = 0

# Clase RobotAgent
# Representa un robot que recoge cajas y las deposita en pallets.
# Hereda de mesa.Agent.
# carrying_box: Indica si el robot está cargando una caja.
# movements: Cuenta los movimientos realizados por el robot.
class RobotAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying_box = False
        self.movements = 0

    # Sentido del entorno: Detecta si hay una caja o un pallet en la celda actual.
    # Retorna dos valores booleanos: (hay_caja, hay_pallet).
    def sense_environment(self):
        cell_content = self.model.grid.get_cell_list_contents([self.pos])
        is_box = any(isinstance(obj, Box) for obj in cell_content)
        is_pallet = any(isinstance(obj, Pallet) for obj in cell_content)
        return is_box, is_pallet

    # Moverse a una posición aleatoria dentro de la vecindad.
    def move(self):
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        new_position = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_position)
        self.movements += 1

    # Recoger una caja si hay una en la posición actual.
    def pick_box(self):
        if not self.carrying_box:
            cell_content = self.model.grid.get_cell_list_contents([self.pos])
            boxes = [obj for obj in cell_content if isinstance(obj, Box)]
            if boxes:
                self.carrying_box = True
                self.model.grid.remove_agent(boxes[0])

    # Soltar una caja en un pallet si está cargando una.
    def drop_box(self):
        if self.carrying_box:
            cell_content = self.model.grid.get_cell_list_contents([self.pos])
            pallets = [obj for obj in cell_content if isinstance(obj, Pallet)]
            if pallets:
                pallets[0].stack_count += 1
                self.carrying_box = False

    # Realiza una acción en cada paso: mover, recoger o soltar cajas.
    def step(self):
        is_box, is_pallet = self.sense_environment()
        if self.carrying_box:
            self.drop_box()
        elif is_box:
            self.pick_box()
        else:
            self.move()

# Clase WarehouseModel
# Modelo principal de la simulación.
# Controla los agentes (robots, cajas, pallets) y el estado de la cuadrícula.
class WarehouseModel(mesa.Model):
    def __init__(self, width, height, num_boxes, num_robots, num_pallets):
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.movements = []  # Lista para registrar movimientos totales.

        # Crear y posicionar cajas.
        for i in range(num_boxes):
            box = Box(i, self)
            self.schedule.add(box)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(box, (x, y))

        # Crear y posicionar pallets.
        for i in range(num_pallets):
            pallet = Pallet(num_boxes + i, self)
            self.schedule.add(pallet)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(pallet, (x, y))

        # Crear y posicionar robots.
        for i in range(num_robots):
            robot = RobotAgent(num_boxes + num_pallets + i, self)
            self.schedule.add(robot)
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(robot, (x, y))

    # Ejecutar un paso de la simulación.
    def step(self):
        self.schedule.step()
        total_movements = sum([robot.movements for robot in self.schedule.agents if isinstance(robot, RobotAgent)])
        self.movements.append(total_movements)

    # Verificar si todas las cajas han sido apiladas en los pallets.
    def all_boxes_stacked(self):
        total_boxes = sum([pallet.stack_count for pallet in self.schedule.agents if isinstance(pallet, Pallet)])
        return total_boxes == 20

# Representación de los agentes en la cuadrícula.
# Asigna formas y colores según el tipo de agente.
def agent_portrayal(agent):
    if isinstance(agent, RobotAgent):
        color = "blue" if agent.carrying_box else "green"
        return {"Shape": "circle", "Color": color, "Layer": 0, "r": 0.5}
    elif isinstance(agent, Box):
        return {"Shape": "rect", "Color": "red", "Layer": 1, "w": 0.6, "h": 0.6}
    elif isinstance(agent, Pallet):
        return {"Shape": "rect", "Color": "yellow", "Layer": 1, "w": 0.6, "h": 0.6}

# Configuración para la visualización interactiva de Mesa.
grid = mesa.visualization.CanvasGrid(agent_portrayal, 10, 10, 500, 500)
model_params = {"width": 10, "height": 10, "num_boxes": 20, "num_robots": 5, "num_pallets": 5}

server = mesa.visualization.ModularServer(
    WarehouseModel,
    [grid],
    "Warehouse Simulation",
    model_params,
)
server.port = 8521

# Simulación en ejecución y recopilación de datos.
model = WarehouseModel(10, 10, 20, 5, 5)

steps = 0  # Contador de pasos.
max_steps = 100  # Máximo de pasos permitidos.

while not model.all_boxes_stacked() and steps < max_steps:
    model.step()
    steps += 1

# Mostrar resultados en consola.
print(f"Tiempo necesario (pasos): {steps}")
print(f"Movimientos totales realizados por los robots: {model.movements[-1]}")

# Visualización de resultados con matplotlib.
plt.figure(figsize=(10, 5))
plt.plot(range(steps), model.movements, label="Movimientos acumulados")
plt.xlabel("Pasos de Simulación")
plt.ylabel("Movimientos Totales")
plt.title("Movimientos de los Robots en el Almacén")
plt.legend()
plt.grid()
plt.show()

# Lanzar el servidor para la visualización interactiva.
server.launch()
