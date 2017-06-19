import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import time
import datetime
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import itertools
import bike


def format_ride(ride):
    """Create a list of strings representing the given ride."""
    time_str_format = '%Y-%m-%d'

    if ride['duration'] != 0:
        speed = '{:.1f}'.format(ride['distance'] / ride['duration'])
    else:
        speed = 'nan'
    elements = [str(ride['id']),
                time.strftime(time_str_format, ride['timestamp']),
                '{:.1f}'.format(ride['distance']),
                '{:.1f}'.format(ride['duration']), speed]
    elements.append(ride['comment'])
    elements.append(ride['url'] != '')
    return elements


class VelociraptorGui(tk.Tk):
    def __init__(self, parent):
        tk.Tk.__init__(self, parent)
        self.parent = parent
        self._initialize()

    def _initialize(self):
        """Setup the GUI widgets.

        +----------------------------------+
        | Add button   Edit button         |
        +----------------------------------+
        |                     |            |
        |                     | Graph view |
        |                     |            |
        |     Rides view      |------------|
        |                     |            |
        |                     | Stats view |
        |                     |            |
        +----------------------------------+

        """
        self.close_button = ttk.Button(self, text='Fermer', command=self.quit)
        self.close_button.grid(column=0, row=0, columnspan=2, sticky='ew')
        self.left_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.left_pane.grid(column=0, row=1, sticky='ewns')
        # self.left_pane.grid_columnconfigure(0, weight=1)
        # self.left_pane.grid_rowconfigure(0, weight=1)
        self._init_rides_view()
        self.right_pane = ttk.PanedWindow(self.left_pane, orient=tk.VERTICAL)
        self.left_pane.add(self.right_pane)
        self._init_graph_view()
        self._init_stats_view()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def _init_rides_view(self):
        colnames = ['id', 'Date', 'Distance (km)', 'Durée (h)',
                    'Vitesse (km/h)', 'Commentaire', 'url']
        self.rides_container = ttk.Frame(self.left_pane)
        self.left_pane.add(self.rides_container)
        self.rides_view = ttk.Treeview(self.rides_container, columns=colnames,
                selectmode='browse')
        self.rides_container.grid_columnconfigure(0, weight=1)
        self.rides_container.grid_rowconfigure(0, weight=1)
        self.rides_view.grid(column=0, row=0, sticky='ewns')

        # Add scrollbars
        vsb = ttk.Scrollbar(self.rides_container, orient='vertical',
                command=self.rides_view.yview)
        hsb = ttk.Scrollbar(self.rides_container, orient='horizontal',
                command=self.rides_view.xview)
        self.rides_view.configure(xscrollcommand=hsb.set,
                yscrollcommand=vsb.set)
        hsb.grid(column=0, row=1, sticky='ew')
        vsb.grid(column=1, row=0, sticky='ns')

        # Populate the view with data
        self.rides = bike.read_db_file()
        for ride in self.rides:
            self.rides_view.insert('', 'end', values=format_ride(ride))

        # Adjust columns
        self.rides_view.column('#0', width=0, stretch=False)
        for col in colnames:
            self.rides_view.heading(col, text=col)
            width = tkfont.Font().measure(col) + 20
            self.rides_view.column(col, minwidth=width, width=width)
        id_width = tkfont.Font().measure('9999') + 20
        self.rides_view.column('id', width=id_width, minwidth=id_width,
                anchor=tk.CENTER)
        date_width = 120
        self.rides_view.column('Date', width=date_width, minwidth=date_width,
                anchor=tk.CENTER)
        for col in ['Distance (km)', 'Durée (h)', 'Vitesse (km/h)']:
            self.rides_view.column(col, anchor=tk.E)

    def _init_graph_view(self):
        cumsum = list(itertools.accumulate(ride['distance'] for ride in
                        self.rides))
        dates = [datetime.datetime.fromtimestamp(time.mktime(ride['timestamp']))
                 for ride in self.rides]
        speeds = [ride['distance'] / ride['duration'] for ride in self.rides]
        plt.style.use('ggplot')
        fig, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(4, 4))
        ax1.plot(dates, cumsum)
        ax2.plot(dates, speeds)
        ax1.set_ylabel('distance (km)')
        ax2.set_ylabel('vitesse (km/h)')
        fig.autofmt_xdate()
        self.graph_view = FigureCanvasTkAgg(fig, master=self.right_pane)
        plt.tight_layout()
        self.graph_view.show()
        # self.graph_view.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        # self.graph_view._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.right_pane.add(self.graph_view.get_tk_widget())

    def _update_stats(self):
        stats = bike.get_stats(self.rides)
        stats_text = 'Distance totale : {:.1f} km\n'.format(stats['tot_distance'])
        stats_text += 'Durée totale : {:.1f} h\n'.format(stats['tot_duration'])
        stats_text += 'Distance moyenne : {:.1f} km\n'.format(stats['mean_distance'])
        stats_text += 'Durée moyenne : {:.1f} h\n'.format(stats['mean_duration'])
        stats_text += 'Vitesse moyenne : {:.2f} km/h\n'.format(stats['speed'])
        self.stats_text.set(stats_text)

    def _init_stats_view(self):
        self.stats_text = tk.StringVar()
        self.stats_view = tk.Label(self.right_pane,
                textvariable=self.stats_text, justify=tk.LEFT, anchor=tk.NW)
        self.right_pane.add(self.stats_view)
        self._update_stats()


if __name__ == '__main__':
    gui = VelociraptorGui(None)
    gui.title('Velociraptor')
    gui.mainloop()
    
