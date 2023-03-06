# Modelo de Robots de limpieza (Roombas)
## Introducción
En este sistema se implementa un modelo multiagente que simula la limpieza de un hotel mediante robots de limpieza
a partir de un porcentaje de suciedad inicial. Los cuartos están representados como un agente diferente a los 
robots, de esta manera, los robots pueden interactuar con los cuartos para limpiarlos por medio de un modelo en 2D.

## Agentes
### Roombas
Los agentes que representarán a los robots pueden estar en 3 diferentes estados:
- Buscando
- Decidiendo
- Limpiando

### Cuartos
Los agentes que representan los cuartos del hotel tienen 2 estados:
- Limpio
- Sucio

### Reglas
Los roombas se pueden mover a través de sus diferentes estados por medio de las siguientes reglas:
1. Siempre tienen como estado inicial "Searching"
2. Al encontrarse en "Searching" los roombas se desplazarán aleatoriamente hasta encontrar un cuarto con estado "Dirty".
3. Si se encuentra un cuarto en "Dirty" y no hay otro Roomba apuntando a ese cuarto, automáticamente el roomba entrara
    dentro del cuarto y lo limpiará cambiando su estado a "Cleaning", en otro caso, si se encuentra a otro roomba que
    apunta al cuarto, ambos entrarán en modo "Debating" donde se decidirá de manera aleatoria quien entrará al cuarto a
    limpiarlo.
4. Una vez se termine de limpiar un cuarto, el roomba cambiará de "Cleaning" a "Searching".

![image](https://github.com/Angelrggarcia/Actividad-integradora/blob/main/Roomba.gif)
