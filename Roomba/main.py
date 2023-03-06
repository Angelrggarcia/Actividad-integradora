import datetime
import random
from enum import IntEnum
from typing import Optional, Tuple
import time
import numpy as np
import matplotlib as mlp
import matplotlib.pyplot as plt
from matplotlib import animation
from mesa import DataCollector
from mesa.agent import Agent
from mesa.model import Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation


class RoombaState(IntEnum):
    SEARCHING = 1
    NEGOTIATING = 2
    CLEANING = 3


class CellState(IntEnum):
    CLEAN = 0
    DIRTY = 1


class RoombaAgent(Agent):
    def __init__(self, unique_id: int, model: Model, grid: MultiGrid):
        super().__init__(unique_id, model)

        self.state = RoombaState.SEARCHING
        self.next_state = None
        self.grid = grid
        self.next_pos: Optional[Tuple[int, int]] = None
        self.negotiate_val: int = 0

    def search_step(self) -> None:
        neighbors = self.grid.get_neighbors(self.pos, moore=True, include_center=False)
        for neighbor_cell in self.grid.iter_neighborhood(self.pos, moore=True, include_center=False):
            cell_contents = self.grid.get_cell_list_contents([neighbor_cell])
            cell_dirty = False
            cell_occupied = False
            for agent in cell_contents:
                if isinstance(agent, CellAgent):
                    cell_dirty = agent.state == CellState.DIRTY
                elif isinstance(agent, RoombaAgent):
                    cell_occupied = True
                    break
            if cell_dirty and not cell_occupied:
                self.next_state = RoombaState.CLEANING
                self.next_pos = neighbor_cell
                return

        selected_cells: int = random.randrange(0, len(neighbors))
        self.next_state = RoombaState.SEARCHING
        self.next_pos = neighbors[selected_cells].pos

    def clean_step(self) -> None:
        cell_contents = self.grid.get_cell_list_contents([self.pos])
        cell_agent = None
        for agent in cell_contents:
            if isinstance(agent, RoombaAgent) and agent is not self:
                self.transition_to_negotiation()
                return
            if isinstance(agent, CellAgent):
                cell_agent = agent
        cell_agent.state = CellState.CLEAN
        self.next_state = RoombaState.SEARCHING
        self.next_pos = self.pos

    def transition_to_negotiation(self):
        self.next_state = RoombaState.NEGOTIATING
        self.next_pos = self.pos
        self.negotiate_val = random.randrange(0, 100)

    def negotiate_step(self) -> None:
        cell_contents = self.grid.get_cell_list_contents([self.pos])
        tied = False
        won = True
        for agent in cell_contents:
            if isinstance(agent, RoombaAgent) and agent is not self:
                if self.negotiate_val == agent.negotiate_val:
                    tied = True
                won = self.negotiate_val >= agent.negotiate_val

        if won and tied:
            self.transition_to_negotiation()
        elif won:
            self.next_state = RoombaState.CLEANING
            self.next_pos = self.pos
        else:
            self.next_state = RoombaState.SEARCHING
            self.next_pos = self.pos

    def step(self) -> None:
        if self.state == RoombaState.SEARCHING:
            self.search_step()
        elif self.state == RoombaState.NEGOTIATING:
            self.negotiate_step()
        elif self.state == RoombaState.CLEANING:
            self.clean_step()

    def advance(self) -> None:
        self.grid.move_agent(self, self.next_pos)
        self.state = self.next_state


class CellAgent(Agent):
    def __init__(self, unique_id: int, model: Model, grid: MultiGrid):
        super().__init__(unique_id, model)

        self.state = CellState.CLEAN
        self.grid = grid


class CleaningModel(Model):
    def __init__(self, width: int, height: int, roombas: int, dirty_chance: float):
        super().__init__()

        self.width = width
        self.height = height
        self.roombas = roombas
        self.num_agents = self.width * self.height
        self.grid = MultiGrid(self.width, self.height, False)
        self.dirty_chance = dirty_chance
        self.data_collector = DataCollector(
            model_reporters={"Cells": self.get_cell_grid,
                             "Roombas": self.get_roomba_grid,
                             'DirtyCells': self.dirty_cell_count}
        )

        self.schedule = SimultaneousActivation(self)

        self.setup()

    def setup(self):
        created_roombas = 0
        for (content, x, y) in self.grid.coord_iter():
            # Put the roombas at the start of the grid
            if created_roombas < self.roombas:
                roomba = RoombaAgent((x, y, 0), self, self.grid)
                self.grid.place_agent(roomba, (x, y))
                self.schedule.add(roomba)
                created_roombas += 1

            # Put a cell in every grid
            cell = CellAgent((x, y, 1), self, self.grid)
            if random.random() < self.dirty_chance:
                cell.state = CellState.DIRTY
            self.grid.place_agent(cell, (x, y))
            self.schedule.add(cell)

    def step(self):
        self.data_collector.collect(self)
        self.schedule.step()

    def get_cell_grid(self):
        grid = np.zeros((self.grid.width, self.grid.height))

        for agents, x, y in self.grid.coord_iter():
            for agent in agents:
                if isinstance(agent, CellAgent):
                    grid[x][y] = int(agent.state)

        return grid

    def get_roomba_grid(self):
        grid = np.zeros((self.grid.width, self.grid.height))

        for agents, x, y in self.grid.coord_iter():
            for agent in agents:
                if isinstance(agent, RoombaAgent):
                    grid[x][y] = int(agent.state)

        return grid

    def dirty_cell_count(self):
        count = 0
        for agents, x, y in self.grid.coord_iter():
            for agent in agents:
                if isinstance(agent, CellAgent):
                    count += agent.state
        return count


def main():
    GRID_SIZE = 15

    NUM_GENERATIONS = 150

    start_time = time.time()

    model = CleaningModel(GRID_SIZE, GRID_SIZE, 4, 0.5)

    for i in range(NUM_GENERATIONS):
        model.step()
    final_time = time.time()

    print('Execution time:', str(datetime.timedelta(seconds=(final_time - start_time))))

    model_data = model.data_collector.get_model_vars_dataframe()

    fig, axs = plt.subplots(nrows=3, ncols=1, figsize=(7, 7))

    axs[0].set_xticks([])
    axs[0].set_yticks([])
    axs[1].set_xticks([])
    axs[1].set_yticks([])

    roomba_colors = []
    cell_colors = []
    roomba_colors.append(np.array([255 / 255, 255 / 255, 255 / 255, 1]))  # No roomba
    roomba_colors.append(np.array([50 / 255, 255 / 255, 50 / 255, 1]))  # Searching
    roomba_colors.append(np.array([255 / 255, 255 / 255, 50 / 255, 1]))  # negotiating
    roomba_colors.append(np.array([50 / 255, 50 / 255, 255 / 255, 1]))  # cleaning
    cell_colors.append(np.array([255 / 255, 255 / 255, 255 / 255, 1]))  # Clean
    cell_colors.append(np.array([169 / 255, 169 / 255, 169 / 255, 1]))  # Dirty
    roomba_cmap = mlp.colors.ListedColormap(roomba_colors)
    cell_cmap = mlp.colors.ListedColormap(cell_colors)

    cells_plot = axs[0].imshow(model.get_cell_grid(), cmap=cell_cmap, vmin=0, vmax=1)
    axs[0].set_title('Cells')
    roombas_plot = axs[1].imshow(model.get_roomba_grid(), cmap=roomba_cmap, vmin=0, vmax=3)
    axs[1].set_title('Roombas')
    model_data['DirtyCells'].iloc[[0]].plot(ax=axs[2])
    axs[2].set_title('Dirty cell count')

    def animate(i):
        roombas_plot.set_data(model_data['Roombas'].iloc[i // 2])
        cells_plot.set_data(model_data['Cells'].iloc[i // 2])
        model_data['DirtyCells'].iloc[0:(i // 2)].plot(ax=axs[2])

    roomba_anim = animation.FuncAnimation(fig, animate, frames=NUM_GENERATIONS * 2)

    roomba_anim.save("animation.mp4")


if __name__ == '__main__':
    main()
