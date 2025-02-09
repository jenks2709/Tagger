import networkx as nx
import matplotlib.pyplot as plt
import json
import pydot
from networkx.drawing.nx_pydot import graphviz_layout
from networkx.readwrite import json_graph

def render_tag_graph(tags=None): #generates an image based on the graph passed to it and saves it to tagGraph.png
    tag_graph = nx.DiGraph()
    if (tags == None) : # if no tag data was passed, read it from file and generate a graph
        tag_data = json.load(open('./tag_data.json', 'r'))
        tag_graph.add_edges_from(tag_data["edges"])
    else: # if tag data was passed, use it to generate  graph
        tag_graph.add_edges_from(tags)

    fig = plt.figure("Tag History", facecolor="#5393f3")
    fig.set_figwidth(1+(2.5 * (nx.number_of_nodes(tag_graph) // nx.dag_longest_path_length(tag_graph)))) # set the width of the diagram to scale with height divided by total nodes 
    fig.set_figheight(1+(nx.dag_longest_path_length(tag_graph) * 1.5)) # set the height of the diagram to scale with the height of the tag tree
    fig.suptitle("Tag History", fontsize="xx-large", fontweight="bold")
    
    plt.xlabel("RHUL Humans vs Zombies", fontsize="xx-large", color="white")# add a label to the bottom of the diagram

    layout=graphviz_layout(tag_graph, prog="dot") # defines positions of nodes to use a hierarchical layout

    nx.draw_networkx(tag_graph, pos=layout, arrows=True, with_labels=True, arrowsize=25, node_size=900, font_size=20, font_color="#0000cc", node_color="#FFC442", node_shape="h", arrowstyle="->", width=2, edge_color="#5C5CD3") # renders tag graph

    ax = plt.gca()
    ax.set_facecolor("#FFC442") # sets the graph background color to orange
    
    # plt.show() # uncomment to show graph in popup window

    plt.savefig("tag_graph_image.png", dpi=200) # save the graph to file

# uncomment below to call function with test data
# tags = [("badspeed", "bergheimer"), ("badspeed", "stewart"), ("badspeed", "mae"), ("mae", "ed"), ("bergheimer", "oli"), ("bergheimer", "logan"), ("logan", "billy"), ("harry", "AJ"), ("harry", "may"), ("AJ", "jasmine"), ("jasmine", "charlotte"), ("charlotte", "joe"), ("joe", "vlad")]
# render_tag_graph()