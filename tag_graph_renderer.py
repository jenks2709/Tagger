import networkx as nx
import matplotlib.pyplot as plt
import pydot
from networkx.drawing.nx_pydot import graphviz_layout

def render_tag_graph(tags): #generates an image based on the graph passed to it and saves it to tagGraph.png
    tag_graph = nx.DiGraph()
    tag_graph.add_edges_from(tags)

    fig = plt.figure("Tag History", facecolor="#5393f3")
    fig.set_figwidth(12)
    fig.set_figheight(nx.dag_longest_path_length(tag_graph) * 1.5) # set the height of the diagram to scale with the height of the tag tree
    fig.suptitle("Tag History", fontsize="xx-large", fontweight="bold")

    layout=graphviz_layout(tag_graph, prog="dot") # defines positions of nodes to use a hierarchical layout

    nx.draw_networkx(tag_graph, pos=layout, arrows=True, with_labels=True, arrowsize=25, node_size=900, font_size=20, font_color="#000066", node_color="#d9ffcc", node_shape="h", arrowstyle="->", width=2, edge_color="#0000cc") # renders tag graph
    
    ax = plt.gca()
    ax.set_facecolor("#d9ffcc") # sets the graph background color to green

    # plt.show() # uncomment to show graph in popup window

    plt.savefig("tagGraph.png", dpi=200) # save the graph to file


# uncomment below to call function with test data
# tags = [("badspeed", "bergheimer"), ("badspeed", "stewart"), ("badspeed", "mae"), ("mae", "ed"), ("bergheimer", "oli"), ("bergheimer", "logan"), ("logan", "billy"), ("harry", "AJ"), ("harry", "may"), ("AJ", "jasmine"), ("jasmine", "charlotte"), ("charlotte", "joe"), ("joe", "vlad")]
# render_tag_graph(tags)
