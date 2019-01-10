import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import datetime
import matplotlib
import matplotlib.style
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import itertools
import bike

# Necessary for py2app to work.
import tkinter.filedialog
import tkinter.messagebox


def format_ride(ride):
    """Create a list of strings representing the given ride."""
    time_str_format = '%Y-%m-%d'

    if ride['duration'] != 0:
        speed = '{:.1f}'.format(ride['distance'] / ride['duration'])
    else:
        speed = 'nan'
    elements = [str(ride['id']),
                ride['timestamp'].strftime(time_str_format),
                '{:.1f}'.format(ride['distance']),
                '{:.1f}'.format(ride['duration']), speed]
    elements.append(ride['comment'])
    elements.append(ride['url'] != '')
    return elements


class RideDetailDialog(tk.Toplevel):
    def __init__(self, parent, title=None, ride=None):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        if ride is not None:
            self.ride = ride
        else:
            self.ride = None

        self.parent = parent

        body = ttk.Frame(self)
        self.initial_focus = self.body(body)
        body.pack(fill=tk.BOTH, ipadx=5, ipady=5)

        self.buttonbox()
        self.grab_set()
        self.result = None

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol('WM_DELETE_WINDOW', self.cancel)

        self.initial_focus.focus_set()
        self.wait_window(self)

    def body(self, master):
        self.fields = []
        for i, field in enumerate(['Date', 'Distance (km)', 'Durée (h)',
            'Commentaire', 'URL']):
            ttk.Label(master, text=field).grid(column=0, row=i, sticky='nsew')
            entry = ttk.Entry(master)
            entry.grid(column=1, row=i, sticky='nsew')
            self.fields.append(entry)
        if self.ride is not None:
            self.fields[0].insert(0,
                    self.ride['timestamp'].strftime(bike.TIMESTR))
            self.fields[1].insert(0, self.ride['distance'])
            self.fields[2].insert(0, self.ride['duration'])
            self.fields[3].insert(0, self.ride['comment'])
            self.fields[4].insert(0, self.ride['url'])
        else:
            timestamp = datetime.datetime.now()
            self.fields[0].insert(0, timestamp.strftime(bike.TIMESTR))
        master.grid_columnconfigure(1, weight=1)
        return self.fields[0]

    def buttonbox(self):
        """Add standard button box."""
        box = ttk.Frame(self)
        w = ttk.Button(box, text='OK', width=10, command=self.ok,
                default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = ttk.Button(box, text='Annuler', width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind('<Return>', self.ok)
        self.bind('<Escape>', self.cancel)

        box.pack(fill=tk.BOTH)

    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set()  # invalid entry, focus back
            return

        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        self.parent.focus_set()
        self.destroy()

    def validate(self):
        valid = True
        self.result = []
        for field in self.fields:
            field.configure(foreground='black')
        try:
            date = datetime.datetime.strptime(self.fields[0].get(),
                    bike.TIMESTR)
            self.result.append(date)
        except ValueError:
            self.fields[0].configure(foreground='red')
            valid = False
        try:
            self.result.append(float(self.fields[1].get()))
        except ValueError:
            self.fields[1].configure(foreground='red')
            valid = False
        try:
            duration = bike.parse_duration(self.fields[2].get())
            self.result.append(duration)
        except ValueError:
            self.fields[2].configure(foreground='red')
            valid = False
        self.result.append(self.fields[3].get())
        self.result.append(self.fields[4].get())
        return valid

    def apply(self):
        if self.ride is not None:
            # Update rides database
            self.ride['timestamp'] = self.result[0]
            self.ride['distance'] = self.result[1]
            self.ride['duration'] = self.result[2]
            self.ride['comment'] = self.result[3]
            self.ride['url'] = self.result[4]
            bike.update_db(self.parent.rides)
        else:
            # Append new ride to database
            bike.add_ride(*self.result)


class VelociraptorGui(tk.Tk):
    def __init__(self, parent):
        tk.Tk.__init__(self, parent)
        self.parent = parent
        self._initialize()
        self.protocol('WM_DELETE_WINDOW', self.quit)
        self.option_add('*tearOff', False)

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
        self.buttonbox()
        self._init_rides_view()
        self._init_graph_view()
        self._init_stats_view()
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.focus_set()

    def buttonbox(self):
        """Add standard button box."""
        box = ttk.Frame(self)
        add_button = ttk.Button(box, text='Ajouter', command=self.add_ride)
        add_button.pack(side=tk.LEFT)
        edit_button = ttk.Button(box, text='Modifier', command=self.edit_ride)
        edit_button.pack(side=tk.LEFT)
        del_button = ttk.Button(box, text='Effacer', command=self.del_ride)
        del_button.pack(side=tk.LEFT)

        self.year = tk.StringVar()
        self.year_combo = ttk.Combobox(box, textvariable=self.year, width=10)
        self.year_combo.bind('<<ComboboxSelected>>', self.change_year)
        self.year_combo.pack(side=tk.RIGHT)
        self.year_combo.state(['readonly'])

        box.grid(column=0, row=0, columnspan=2, sticky='ew', ipadx=5, ipady=5)

    def _init_rides_view(self):
        colnames = ['id', 'Date', 'Distance (km)', 'Durée (h)',
                    'Vitesse (km/h)', 'Commentaire', 'url']
        self.rides_container = ttk.Frame(self)
        self.rides_container.grid(column=0, row=1, rowspan=2, sticky='ewns')
        self.rides_view = ttk.Treeview(self.rides_container, columns=colnames,
                selectmode='browse')
        # Make rides view resizable.
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

        # Adjust columns
        self.rides_view.column('#0', width=0, stretch=False)
        for col in colnames:
            self.rides_view.heading(col, text=col)
            width = tkfont.Font().measure(col) + 10
            self.rides_view.column(col, minwidth=width, width=width)
        id_width = tkfont.Font().measure('9999') + 10
        self.rides_view.column('id', width=id_width, minwidth=id_width,
                anchor=tk.CENTER)
        date_width = 100
        self.rides_view.column('Date', width=date_width, minwidth=date_width,
                anchor=tk.CENTER)
        comment_width = 160
        self.rides_view.column('Commentaire', width=comment_width,
                minwidth=comment_width)
        for col in ['Distance (km)', 'Durée (h)', 'Vitesse (km/h)']:
            self.rides_view.column(col, anchor=tk.E)

        # Bind double click events
        self.rides_view.bind('<Double-1>', self.edit_ride)

        # Populate the view with data
        self.year.set(str(datetime.datetime.now().year))
        self.load_data()
        self.update_rides_view()
        if self.years:
            self.year.set(self.years[0])

    def change_year(self, event):
        self.update_rides_view()
        self.update_graph_view()
        self.update_stats()

    def load_data(self):
        self.rides = bike.read_db_file(year='all')
        self.years = sorted(list(set(ride['timestamp'].year for ride in
            self.rides)), reverse=True)
        self.year_combo['values'] = self.years

    def update_rides_view(self):
        self.viewable_rides = [ride for ride in self.rides if
                ride['timestamp'].year == int(self.year.get())]
        self.rides_view.delete(*self.rides_view.get_children())
        for ride in self.viewable_rides:
            self.rides_view.insert('', 'end', values=format_ride(ride))

    def get_graph_data(self):
        cumsum = list(itertools.accumulate(ride['distance'] for ride in
                        self.viewable_rides))
        dates = [ride['timestamp'] for ride in self.viewable_rides]
        speeds = [ride['distance'] / ride['duration'] for ride in
                self.viewable_rides]
        return cumsum, dates, speeds

    def update_graph_view(self):
        cumsum, dates, speeds = self.get_graph_data()
        self.ax1.clear()
        self.ax2.clear()
        self.ax1.plot(dates, cumsum)
        self.ax2.plot(dates, speeds)
        self.ax1.set_ylabel('distance (km)')
        self.ax2.set_ylabel('vitesse (km/h)')
        self.fig.autofmt_xdate()
        self.graph_view.draw()
        
    def _init_graph_view(self):
        matplotlib.style.use('ggplot')
        self.fig = Figure(figsize=(4, 4), tight_layout=True)
        cumsum, dates, speeds = self.get_graph_data()
        self.ax1, self.ax2 = self.fig.subplots(2, sharex=True)
        self.ax1.plot(dates, cumsum)
        self.ax2.plot(dates, speeds)
        self.ax1.set_ylabel('distance (km)')
        self.ax2.set_ylabel('vitesse (km/h)')
        self.fig.autofmt_xdate()
        self.graph_view = FigureCanvasTkAgg(self.fig, master=self)
        self.graph_view.draw()

        self.graph_view.get_tk_widget().grid(column=1, row=1, sticky='nsew')

    def update_stats(self):
        stats = bike.get_stats(self.viewable_rides)
        stats_text = 'Distance totale : {:.1f} km\n'.format(stats['tot_distance'])
        stats_text += 'Durée totale : {:.1f} h\n'.format(stats['tot_duration'])
        stats_text += 'Distance moyenne : {:.1f} km\n'.format(stats['mean_distance'])
        stats_text += 'Durée moyenne : {:.1f} h\n'.format(stats['mean_duration'])
        stats_text += 'Vitesse moyenne : {:.2f} km/h\n'.format(stats['speed'])
        self.stats_text.set(stats_text)

    def _init_stats_view(self):
        self.stats_text = tk.StringVar()
        self.stats_view = tk.Label(self, textvariable=self.stats_text,
                justify=tk.LEFT, anchor=tk.NW)
        self.stats_view.grid(column=1, row=2)
        self.update_stats()

    def add_ride(self):
        dialog = RideDetailDialog(self, 'Ajouter une randonnée')
        result = dialog.result
        dialog.destroy()
        if result:
            self.load_data()
            self.update_rides_view()
            self.update_graph_view()
            self.update_stats()

    def edit_ride(self, event=None):
        try:
            iid = self.rides_view.selection()[0]
        except IndexError:
            return
        rideid = int(self.rides_view.item(iid, 'values')[0])
        ride = self.rides[rideid]
        dialog = RideDetailDialog(self, 'Modifier une randonnée', ride=ride)
        result = dialog.result
        dialog.destroy()
        if result:
            self.load_data()
            self.update_rides_view()
            self.update_graph_view()
            self.update_stats()

    def del_ride(self):
        try:
            iid = self.rides_view.selection()[0]
        except IndexError:
            return
        rideid = int(self.rides_view.item(iid, 'values')[0])
        self.rides.pop(rideid)
        bike.update_db(self.rides)
        self.load_data()
        self.update_rides_view()
        self.update_graph_view()
        self.update_stats()

if __name__ == '__main__':
    gui = VelociraptorGui(None)
    gui.title('Velociraptor')
    gui.mainloop()
    
