This addon is a proff of concept for using graph in GRAMPS.
it s an alpha plugin to demonstrate the use of graph

It create a dotfile of the relation beetween the Home person and the active person. 
Here is the variable that should be set in the code

maxdepth : maximum distance to find the relationship with the common ancestor
dotfile : the name of the dot file generated

you can generate a png image with the command

dot -T png -o pngfile dotfile.dot
