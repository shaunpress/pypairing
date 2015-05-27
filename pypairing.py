import wx
import wx.html
import wx.grid
import copy

FONTSIZE = 10
''' Create some Menu Constants '''
ID_NEW_TOURNAMENT = wx.NewId()
ID_SAVE_TOURNAMENT = wx.NewId()
ID_MODIFY_TOURNAMENT = wx.NewId()
ID_DELETE_ROUND = wx.NewId()
ID_ADD_PLAYER = wx.NewId()
ID_DELETE_PLAYER = wx.NewId()
ID_STANDINGS = wx.NewId()
ID_CROSSTABLE = wx.NewId()
ID_SHOW_PAIRING = wx.NewId()
ID_CSV_EXPORT = wx.NewId()
ID_HELP = wx.NewId()
ID_ABOUT = wx.NewId()


''' Some general functions to do stuff '''

def get_DateTime(time_string):
    year,month,day = time_string.split('-')
    date = wx.DateTime()
    date.Set(int(day),int(month),int(year))
    return date

def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)

def make_printer_text(text_string):
    ''' A function that turns tabs into spaces
        It takes a string and breaks it up to fixed
        sized fields and replaces tabs with spaces
        Tabs are used as field delimiters '''
    FIELD_SIZE = 8
    field_width = []
    line_list = text_string.split('\n')
    #First line is assumed to be field headings
    field_list = line_list[0].split('\t')
    for fields in field_list:
        tab_num = (len(fields)+FIELD_SIZE-1)/FIELD_SIZE
        field_width.append(tab_num)

    for i in range(1,len(line_list)):
        if line_list[i].startswith("==="):
            #ignore === line breaks
            continue
        field_list = line_list[i].split('\t')
        for j in range(len(field_list)):
            tab_num = (len(field_list[j])+FIELD_SIZE-1)/FIELD_SIZE
            if tab_num > field_width[j]:
                field_width[j] = tab_num

    for i in range(len(field_width)):
        field_width[i] = field_width[i]*FIELD_SIZE

    output_string = ""
    for lines in line_list:
        if lines.startswith("==="):
            output_string += lines
        else:
            field_list = lines.split('\t')
            for i in range(len(field_list)):
                extra_spaces = field_width[i]-len(field_list[i])
                output_string += field_list[i]+" "*extra_spaces

        output_string += "\n"

    return output_string
            

def Warn(parent, message, caption = 'Warning!'):
    dlg = wx.MessageDialog(parent, message, caption, wx.OK | wx.ICON_WARNING)
    dlg.ShowModal()
    dlg.Destroy()
    
''' App classes '''

class MyApp(wx.App):
    """ The basic app class to run this app
    """

    def OnInit(self):
        self.frame = MainFrame(None,title="Py Pairing 1.0",size=(720,720))
        self.SetTopWindow(self.frame)
        self.frame.Show()

        return True


class MainFrame(wx.Frame):
    def __init__(self,*args,**kwargs):
        super(MainFrame,self).__init__(*args,**kwargs)

        self.app_page = None
        self.frame_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.frame_sizer)
        self.make_menu()
        self.init_mvc()

        self.make_dialogs()


    def init_mvc(self):
        ''' This should set up new data structures every time a new file is loaded etc '''

        if self.app_page:
            self.app_page.Destroy()
            
        self.tournament_details = TournamentClass()
        self.player_details = PlayerListClass()
        self.tournament_pairings = PairingListClass()

        self.view = None
        self.app_page = MyTabFrame(self,self.player_details,self.tournament_pairings)
        self.app_page.SetMinSize(wx.Size(640,640))
        self.frame_sizer.Add(self.app_page,1,wx.EXPAND)
        self.Layout()
        
    def make_menu(self):
        menu_bar = wx.MenuBar()

        #File Menu
        file_menu = wx.Menu()
        file_menu.Append(ID_NEW_TOURNAMENT,"New Tournament\tCtrl+N")
        file_menu.Append(wx.ID_OPEN,"Open Tournament\tCtrl+O")
        file_menu.Append(ID_SAVE_TOURNAMENT,"Save Tournament\tCtrl+S")
        file_menu.AppendSeparator()
        file_menu.Append(ID_MODIFY_TOURNAMENT,"Modify Current Tournament")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT,"Exit\tCtrl+E")
        

        menu_bar.Append(file_menu,"&File")

        #Standings Menue
        standings_menu = wx.Menu()
        standings_menu.Append(ID_STANDINGS,"Standings")
        standings_menu.Append(ID_CROSSTABLE,"Crosstable")
        standings_menu.Append(ID_SHOW_PAIRING,"Pairings")
        menu_bar.Append(standings_menu,"Standings")
        

        #Extras Menu
        extras_menu = wx.Menu()
        extras_menu.Append(ID_DELETE_ROUND,"Delete current round")
        extras_menu.AppendSeparator()
        extras_menu.Append(ID_CSV_EXPORT,"Export Tournament in CSV format")

        menu_bar.Append(extras_menu,"Extras")

        #Help Menu
        help_menu = wx.Menu()
        help_menu.Append(ID_HELP,"Help")
        help_menu.Append(ID_ABOUT,"About")
        menu_bar.Append(help_menu,"Help")

        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU,self.OnMenu)

    def make_dialogs(self):
        self.details_dialog = TournamentDetailsDialog()

    def OnMenu(self,event):
        ''' Handle all the menu events in the main frame '''
        evt_id = event.GetId()
        if evt_id == ID_NEW_TOURNAMENT:
            self.new_tournament()
        elif evt_id == wx.ID_OPEN:
            self.open_tournament()
        elif evt_id == ID_SAVE_TOURNAMENT:
            self.save_tournament()
        elif evt_id == ID_MODIFY_TOURNAMENT:
            self.modify_tournament()
        elif evt_id == wx.ID_EXIT:
            ret_value = self.exit_app()
            if ret_value:
                self.Destroy()
        elif evt_id == ID_STANDINGS:
            self.app_page.SetSelection(2)
            self.app_page.show_standings()
        elif evt_id == ID_CROSSTABLE:
            self.app_page.SetSelection(2)
            self.app_page.show_crosstable()
        elif evt_id == ID_SHOW_PAIRING:
            self.app_page.SetSelection(2)
            self.app_page.show_pairings()
        elif evt_id == ID_DELETE_ROUND:
            self.delete_last_round()
        elif evt_id == ID_CSV_EXPORT:
            self.export_csv()
        elif evt_id == ID_HELP:
            self.showHelp()
        elif evt_id == ID_ABOUT:
            self.showAbout()
        else:
            event.Skip()

    def new_tournament(self):
        self.details_dialog.t_name_txt.SetValue("")
        self.details_dialog.place_txt.SetValue("")
        self.details_dialog.rounds_num.SetValue("")
        self.details_dialog.director_txt.SetValue("")
        if self.details_dialog.ShowModal() == wx.ID_OK:
            dlg_data = (self.details_dialog.t_name_txt.GetValue(),
                        self.details_dialog.place_txt.GetValue(),
                        self.details_dialog.begin_date.GetValue().FormatISODate(),
                        self.details_dialog.end_date.GetValue().FormatISODate(),
                        self.details_dialog.rounds_num.GetValue(),
                        self.details_dialog.director_txt.GetValue())
            self.tournament_details.set_details(dlg_data)
            self.init_mvc()
            
        self.details_dialog.Hide()
        
    def modify_tournament(self):
        if self.details_dialog.ShowModal() == wx.ID_OK:
            dlg_data = (self.details_dialog.t_name_txt.GetValue(),
                        self.details_dialog.place_txt.GetValue(),
                        self.details_dialog.begin_date.GetValue().FormatISODate(),
                        self.details_dialog.end_date.GetValue().FormatISODate(),
                        self.details_dialog.rounds_num.GetValue(),
                        self.details_dialog.director_txt.GetValue())
            self.tournament_details.set_details(dlg_data)
            
        self.details_dialog.Hide()

    def open_tournament(self):
        dlg = wx.FileDialog(self,"Open File",style=wx.FD_OPEN,wildcard="*.aps")
        if dlg.ShowModal() == wx.ID_OK:
            self.reset_tournament()
            fname = dlg.GetPath()
            self.read_file(fname)
            if self.view != None:
                self.view.Destroy()

    def save_tournament(self):
        dlg = wx.FileDialog(self,"Write File",style=wx.FD_SAVE,wildcard="*.aps")
        if dlg.ShowModal() == wx.ID_OK:
            fname = dlg.GetPath()
            self.write_file(fname)
            print self.tournament_details.file_output()
            if self.view != None:
                self.view.Destroy()

    def write_file(self,fname):
        f = open(fname,'w')
        f.write(self.tournament_details.file_output())
        f.write(self.player_details.file_output())
        f.write(self.player_details.file_pairing_output())
        f.close()

    def read_file(self,fname):
        # Reads the file in APS (Abstract Pairing System) Format
        f = open(fname,'r')
        lines = f.read().splitlines()
        f.close()
        date_line = lines[2].split(',')
        tournament_info = (lines[0],lines[1],date_line[0],date_line[1],lines[4],lines[3])
        self.tournament_details.set_details(tournament_info)
        self.details_dialog.set_values(tournament_info)
        self.player_details.reset_players()

        if len(lines) <= 6:
            #No Players!
            return
        line_count = 6
        while lines[line_count] != '':
            player_line = tuple(lines[line_count].split(';'))
            self.player_details.add_player(player_line)
            line_count += 1

        msg = wx.grid.GridTableMessage(self.app_page.player_panel.player_list_table,
                                 wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,line_count-6)
        self.app_page.player_panel.player_grid.ProcessTableMessage(msg)
        #self.app_page.player_panel.player_grid.ForceRefresh()


        line_count += 2
        self.tournament_pairings.clear_entries()
        while lines[line_count] != '':
            print lines[line_count]
            pairing_line = lines[line_count].split()
            print pairing_line
            player_id = int(pairing_line[0])
            player_score = 0
            for i in range(1,len(pairing_line)):
                info = pairing_line[i].split(";")
                round_data = [info[0],self.player_details.players[player_id].name,player_score,info[1],info[2],0,player_id]
                print round_data
                self.player_details.players[player_id].enter_results(i,round_data)
                self.tournament_pairings.load_pairing(i,round_data)
                player_score += num(info[1])
            line_count += 1

        self.tournament_pairings.sort_pairings()
        total_rounds = len(pairing_line)-1
        self.app_page.round_panel.round_spinner.SetRange(0,total_rounds)
        self.update_score_totals()

    def update_score_totals(self):
        self.tournament_pairings.calc_round_totals()
        for player in self.player_details.players:
            for result_entry in player.results:
                if result_entry.table_no != 'X':
                    result_entry.vp_total = self.tournament_pairings.tournament_pairings[result_entry.round_no-1].board_totals[num(result_entry.table_no)-1]
                    print player.name,result_entry.vp_total
        
    def reset_tournament(self):
        self.app_page.Destroy()
        self.init_mvc()

    def delete_last_round(self):
        self.app_page.round_panel.delete_round()
    
    def export_csv(self):
        print self.player_details.player_csv()
    
    def showHelp(self):
        helpDlg = HelpFrameClass(None)
        helpDlg.Show()
        
    def showAbout(self):
        print "About:"
        info = wx.AboutDialogInfo()
        desc = ["\nPyPairing\n",
                "Platform Info: Python 2.7 wxPython 2.8",
                "License: Public Domain"]
        print desc
        desc = "\n".join(desc)
        
        info.SetName("PyPairing")
        info.SetVersion("1.0")
        info.SetCopyright("Shaun Press shaunpress@gmail.com")
        info.SetDescription(desc)
        
        print desc
        wx.AboutBox(info)
        

    def exit_app(self):
        return True


class MyTabFrame(wx.Notebook):
    def __init__(self,parent,data_source,pairing_source):
        super(MyTabFrame,self).__init__(parent)

        self.player_list_data = data_source
        self.pairing_list_data = pairing_source
        self.player_panel = PlayerListPage(self,data_source)

        
        self.round_panel = PairingPage(self,pairing_source)
        self.output_panel = OutputPage(self)

        #Set up tabs
        self.AddPage(self.player_panel,"Player List")
        self.AddPage(self.round_panel,"Pairing Page")
        self.AddPage(self.output_panel,"Output")

    def reset_data(self,player_data,pairing_data):
        self.player_list_data = player_data
        self.pairing_list_data = pairing_data
        self.player_panel.reset_data(player_data,pairing_data)
        self.round_panel.reset_data(player_data,pairing_data)
        self.output_panel.reset_data(player_data,pairing_data)
        
    def show_standings(self):
        self.output_panel.show_standings(None)
        
    def show_crosstable(self):
        self.output_panel.show_crosstable()
        
    def show_pairings(self):
        self.output_panel.show_pairings()

class PlayerListPage(wx.Panel):
    def __init__(self,parent,data_source):
        super(PlayerListPage,self).__init__(parent)

        self.pairing_list_data = parent.pairing_list_data
        self.player_list_data = data_source

        #Add the player list grid
        self.player_list_table = PlayerListTable(data_source,self.pairing_list_data)
        self.player_grid = wx.grid.Grid(self,size=(640,480))
        self.player_grid.SetTable(self.player_list_table,True)

        self.player_grid.SetColSize(0,200)
        
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK,self.mouse_clicked,self.player_grid)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.player_grid,0,wx.ALL|wx.EXPAND,5)

        #Add some buttons

        self.add_button = wx.Button(self,ID_ADD_PLAYER,"Add Player")
        self.Bind(wx.EVT_BUTTON,self.add_player_clicked, self.add_button)
        self.delete_button = wx.Button(self,ID_DELETE_PLAYER,"Delete Player")
        self.Bind(wx.EVT_BUTTON,self.delete_player_clicked, self.delete_button)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.add_button,0,wx.ALL,5)
        button_sizer.Add(self.delete_button,0,wx.ALL,5)

        box.Add(button_sizer,0,wx.EXPAND)
        
        self.SetSizer(box)
        self.Layout()

    def reset_data(self,player_data,pairing_data):
        self.pairing_list_data = pairing_data
        msg = wx.grid.GridTableMessage(self.player_list_table,
                                 wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,0,self.player_list_table.GetNumberRows())
        self.player_grid.ProcessTableMessage(msg)
        self.player_list_table.addDataSource(player_data)

    def add_player_clicked(self,event):
        self.player_list_table.AppendRows()
        self.add_unplayed_rounds()
        msg = wx.grid.GridTableMessage(self.player_list_table,
                                 wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,1)
        self.player_grid.ProcessTableMessage(msg)
        
    def add_unplayed_rounds(self):
        ''' Should only be called after a new player is added '''
        last_player = self.player_list_data.players[-1]
        for i in range(self.pairing_list_data.total_rounds):
            self.pairing_list_data.tournament_pairings[i].add_pairing(["X",last_player.name,0,0,0,0,last_player.pairing_id])
        

    def delete_player_clicked(self,event):

        if self.pairing_list_data.total_rounds > 0:
            ''' We have started pairing, so no deletion possible'''
            dlg = wx.MessageBox("Cannot remove players once event has started",
                                "Delete player warning", wx.OK | wx.ICON_EXCLAMATION)

            return
        
        player_row = self.player_grid.GetSelectedRows()
        if not player_row:
            return
        retcode = wx.MessageBox("Do you wish to delete this player?",
                                "Delete Player", wx.YES_NO | wx.ICON_QUESTION)
        if retcode == wx.YES:
            print "Delete"
            for row in reversed(player_row):
                self.player_list_table.DeleteRows(row,1)

                msg = wx.grid.GridTableMessage(self.player_list_table,
                                 wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,row,1)
                self.player_grid.ProcessTableMessage(msg)

    def mouse_clicked(self,event):
        x, y = event.GetRow(),event.GetCol()
        if x < 0:
            return
        availibility_dialog = PlayerAvailibilityDialog(self.player_list_data.players[x])
        if availibility_dialog.ShowModal() == wx.ID_OK:
            i = 0
            for checkbox in availibility_dialog.checkboxes:
                self.player_list_data.players[x].availibility[i] = checkbox.GetValue()
                i += 1
                
                  
class PlayerListTable(wx.grid.PyGridTableBase):
    def __init__(self,data_source,pairing_source):
        wx.grid.PyGridTableBase.__init__(self)

        self.colLabels = ["Name","Rating","Notes"]
        self.data = data_source
        self.pairing_list = pairing_source

        self.number_of_rows = len(self.data.players)

        self.odd = wx.grid.GridCellAttr()
        self.odd.SetBackgroundColour("sky blue")
        self.odd.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.BOLD))

        self.even = wx.grid.GridCellAttr()
        self.even.SetBackgroundColour("light blue");
        self.even.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.BOLD))

    def addDataSource(self,data):
        ''' Add the data source to this control '''
        self.data = data

    def GetNumberRows(self):
        return self.data.total_players

    def GetNumberCols(self):
        return 3

    def AppendRows(self,numRows=1):
        self.number_of_rows += numRows
        self.data.new_player()
        return True

    def DeleteRows(self,pos=0,numRows=1):
        self.number_of_rows -= numRows
        self.data.remove_player(pos)
        print self.GetNumberRows()
        for i in range(self.GetNumberRows()):
            for j in range(self.GetNumberCols()):
                print self.GetValue(i,j),
            print
            
        return True

    def IsEmptyCell(self,row,col):
        return self.data.players[row] is not None

    def GetValue(self,row,col):
        if not self.data:
            return ''
        value = self.data.players[row].get_value_n(col)
        if value is not None:
            return value
        else:
            return ''

    def GetColLabelValue(self,col):
        return self.colLabels[col]
    
    def SetValue(self,row,col,value):
        self.data.players[row].set_value_n(col,value)
        if col == 0:
            #Player name has changed, need to update pairings as well
            player_id = row
            self.pairing_list.update_names(player_id,value)
            

    def GetAttr(self,row,col, kind):
        attr = [self.even, self.odd][row % 2]
        attr.IncRef()
        return attr

class PairingPage(wx.Panel):
    def __init__(self,parent,data_source):
        super(PairingPage,self).__init__(parent)

        self.pairs_shown = 0
        self.display_panel = wx.Panel(self,size=(640,480))
        self.player_details_list = parent.player_list_data
        self.pairing_list_table = PairingListTable(data_source)
        self.pairing_list_grid = wx.grid.Grid(self.display_panel,size=(640,480))
        self.pairing_list_grid.SetTable(self.pairing_list_table,True)

        self.pairing_list_grid.SetColSize(1,200)
        
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.display_panel,0,wx.ALL|wx.EXPAND,5)

        #Add some buttons
        self.auto_btn = wx.Button(self,-1,"Automatic")
        self.Bind(wx.EVT_BUTTON,self.automatic_clicked, self.auto_btn)
        self.modify_btn = wx.Button(self,-1,"Modify")
        self.Bind(wx.EVT_BUTTON,self.modify_clicked, self.modify_btn)
        self.print_btn = wx.Button(self,-1,"Print")
        self.Bind(wx.EVT_BUTTON,self.print_pairings,self.print_btn)
        self.update_btn = wx.Button(self,-1,"Update")
        self.Bind(wx.EVT_BUTTON,self.update_clicked, self.update_btn)

        button_sizer = wx.FlexGridSizer(2,2,5,5)
        button_sizer.Add(self.auto_btn,0,wx.ALL,5)
        button_sizer.Add(self.modify_btn,0,wx.ALL,5)
        button_sizer.Add(self.update_btn,0,wx.ALL,5)
        button_sizer.Add(self.print_btn,0,wx.ALL,5)

        bottom_bar = wx.BoxSizer(wx.HORIZONTAL)
        bottom_bar.Add(button_sizer,0,wx.EXPAND)

        #Add a spinner for rounds

        self.round_spinner = wx.SpinCtrl(self,-1,"",size=(80,30),min=0,max=0,initial=0)
        self.Bind(wx.EVT_SPINCTRL,self.round_changed,self.round_spinner)

        bottom_bar.Add(self.round_spinner,0,wx.RIGHT)

        box.Add(bottom_bar,0,wx.ALL,5)

        self.SetSizer(box)
        self.Layout()

    def reset_data(self,player_data,pairing_data):
        #self.pairing_list_table.Destroy()
        self.pairing_list_table = PairingListTable(pairing_data)
        self.player_details_list = player_data
        self.pairing_list_grid = wx.grid.Grid(self.display_panel,size=(640,480))
        self.pairing_list_grid.SetTable(self.pairing_list_table,True)
        
    def automatic_clicked(self,event):
        if self.round_spinner.GetValue() < self.pairing_list_table.data.total_rounds:
            Warn(self,"Cannot pair a previous round")
            #Do not pair for previous rounds
            return
        
        if len(self.player_details_list.players) == 0:
            Warn(self,"No players entered for this event")
            return
        self.pairing_list_table.data.new_round()
        pairing_list = self.make_pairings()
        msg = wx.grid.GridTableMessage(self.pairing_list_table,
                                 wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,0,self.pairs_shown)
        self.pairing_list_grid.ProcessTableMessage(msg)
        self.pairs_shown = len(pairing_list)
        self.pairing_list_table.data.add_pairing(self.pairing_list_table.data.total_rounds-1,pairing_list)
        msg = wx.grid.GridTableMessage(self.pairing_list_table,
                                 wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,self.pairs_shown)
        self.pairing_list_grid.ProcessTableMessage(msg)
        self.round_spinner.SetRange(0,self.pairing_list_table.data.total_rounds)
        self.round_spinner.SetValue(self.pairing_list_table.data.total_rounds)
        self.pairing_list_table.ChangeCurrentRound(self.pairing_list_table.data.total_rounds)
        self.update_clicked(None)

    def round_changed(self,event):
        new_round = self.round_spinner.GetValue()
        self.pairing_list_table.ChangeCurrentRound(new_round)
        self.update_clicked(event)
        
    def delete_round(self):
        ''' Removes most recent paired round '''
        new_round = self.round_spinner.GetValue()
        if self.pairing_list_table.data.delete_round():
            self.player_details_list.delete_round()
            self.pairing_list_table.ChangeCurrentRound(new_round-1)
            self.round_spinner.SetValue(new_round-1)
            self.round_spinner.SetRange(0,self.pairing_list_table.data.total_rounds)
            self.update_clicked(None)
        else:
            dlg = wx.MessageBox("Can only delete last paired round",
                                "Delete Round Warning", wx.OK | wx.ICON_EXCLAMATION)

    
    def modify_clicked(self,event):
        ''' Brings up a dialog to allow pairings to be changed '''
        dlg = ModifyPairingDialog(self.pairing_list_table.data)
        dlg.ShowModal()
        self.pairing_list_table.sort_pairings()
        
    def update_clicked(self,event):
        ''' Update the players data with results from the displayed round
            Called when update button is clicked or when round spinner
            changes '''

        for pairing in self.pairing_list_table.GetCurrentPairings():
            self.player_details_list.players[pairing[6]].enter_results(self.pairing_list_table.current_round,pairing)

        self.update_score_totals()    
        self.show_round_pairings()

    def update_score_totals(self):
        self.pairing_list_table.data.calc_round_totals()
        for player in self.player_details_list.players:
            for result_entry in player.results:
                if result_entry.table_no != 'X':
                    result_entry.vp_total = self.pairing_list_table.data.tournament_pairings[result_entry.round_no-1].board_totals[num(result_entry.table_no)-1]

    def show_round_pairings(self):
        ''' Updates result table for current round '''   
        msg = wx.grid.GridTableMessage(self.pairing_list_table,
                                 wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED,0,self.pairs_shown)
        self.pairing_list_grid.ProcessTableMessage(msg)
        self.pairs_shown = self.pairing_list_table.data.current_pairing_total()
        msg = wx.grid.GridTableMessage(self.pairing_list_table,
                                 wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,self.pairs_shown)
        self.pairing_list_grid.ProcessTableMessage(msg)
            
    def make_pairings(self):
        pairing_data = []
        for i in range(len(self.player_details_list.players)):
            player_id = self.player_details_list.players[i].pairing_id
            player_score = self.player_details_list.players[i].get_player_score()
            pairing_data.append([player_id,self.player_details_list.players[i],player_score[0],player_score[1]])

            
        simple_pairings = SimplePairingClass(self.pairing_list_table.current_round,pairing_data)
        pairings = simple_pairings.make_pairing()
        return pairings
    
    def print_pairings(self,event):
        header_text = "Parings for Round: "+str(self.pairing_list_table.data.current_round)+"\n"
        output_text = "Board \tPlayer \tCurrent Score \tMP \tVP\n"
        output_text += "=====================================================\n"

        round_pairings = self.pairing_list_table.data.GetRoundPairingList(self.pairing_list_table.data.current_round)
        if len(round_pairings) > 0:
            current_board = round_pairings[0][0]

            for pairing in round_pairings:
                if pairing[0] != current_board:
                    output_text += "=====================================================\n"
                    current_board = pairing[0]
                output_text += str(pairing[0])+"\t"+pairing[1]+"\t"+str(pairing[2])+"\t .... \t ... \n"
        print_output = make_printer_text(output_text)
        display_text = header_text+print_output
        
        print display_text
        
        pdata = wx.PrintData()
        pdata.SetPaperId(wx.PAPER_A4)
        pdata.SetOrientation(wx.PORTRAIT)
        margins = (wx.Point(15,15),wx.Point(15,15))
        
        data = wx.PrintDialogData(pdata)
        printer = wx.Printer(data)
        printout = TextPrintout(display_text,"Py Pairing 1.0", margins)
        useSetupDialog = True
        if not printer.Print(self, printout, useSetupDialog) and printer.GetLastError() == wx.PRINTER_ERROR:
            wx.MessageBox("Problem with printer","Printing Error",wx.OK)
        else:
            data = printer.GetPrintDialogData()
            pdata = wx.PrintData(data.GetPrintData())
        printout.Destroy()
            

class PairingListTable(wx.grid.PyGridTableBase):
    def __init__(self,data_source):
        wx.grid.PyGridTableBase.__init__(self)

        self.colLabels = ["Board","Player","Score","Match Points","Victory Points"]
        self.data = data_source
        self.current_round = 0

        self.number_of_rows = 0

        self.odd = wx.grid.GridCellAttr()
        self.odd.SetBackgroundColour("sky blue")
        self.odd.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.BOLD))

        self.even = wx.grid.GridCellAttr()
        self.even.SetBackgroundColour("light blue");
        self.even.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.BOLD))

    def GetNumberRows(self):
        return self.data.current_pairing_total()

    def GetNumberCols(self):
        return 5

    def AppendRows(self,numRows=1):
        self.number_of_rows += numRows
        return True

    def DeleteRows(self,pos=0,numRows=1):
        self.number_of_rows -= numRows
        return True

    def IsEmptyCell(self,row,col):
        return len(self.data.tournament_pairings[self.current_round-1].pairings) < row

    def GetValue(self,row,col):
        if not self.data:
            return ''
        value = self.data.tournament_pairings[self.current_round-1].pairings[row][col]
        if value is not None:
            return value
        else:
            return ''

    def GetColLabelValue(self,col):
        return self.colLabels[col]
    
    def SetValue(self,row,col,value):
        self.data.tournament_pairings[self.current_round-1].set_value_n(row,col,value)

    def GetAttr(self,row,col, kind):
        attr = [self.even, self.odd][row % 2]
        if col < 3:
            attr.SetReadOnly(True)
        else:
            attr.SetReadOnly(False)
        attr.IncRef()
        return attr

    def GetCurrentPairings(self):
        return self.data.GetCurrentPairingList()

    def ChangeCurrentRound(self,new_round):
        self.current_round = new_round
        self.data.current_round = new_round
        
    def sort_pairings(self):
        self.data.sort_pairings()

class OutputPage(wx.Panel):
    def __init__(self,parent):
        super(OutputPage,self).__init__(parent)

        self.player_list_data = parent.player_list_data
        self.pairing_list_data = parent.pairing_list_data

        box = wx.BoxSizer(wx.VERTICAL)
        self.create_button_bar(box)

        self.create_output_window(box)

        self.SetSizer(box)
        self.Layout()

    def reset_data(self,player_data,pairing_data):
        self.player_list_data = player_data
        self.pairing_list_data = pairing_data

    def create_button_bar(self,parent_sizer):
        
        self.standings_button = wx.Button(self,ID_STANDINGS,"Standings")
        self.Bind(wx.EVT_BUTTON,self.show_standings,self.standings_button)
        self.crosstable_button = wx.Button(self,ID_CROSSTABLE,"Crosstable")
        self.Bind(wx.EVT_BUTTON,self.show_crosstable,self.crosstable_button)
        self.show_pairing_button = wx.Button(self, ID_SHOW_PAIRING,"Pairings")
        self.Bind(wx.EVT_BUTTON,self.show_pairings,self.show_pairing_button)
        self.print_button = wx.Button(self,-1,"Print")
        self.Bind(wx.EVT_BUTTON,self.on_print,self.print_button)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.standings_button,0,wx.ALL,5)
        button_sizer.Add(self.crosstable_button,0,wx.ALL,5)
        button_sizer.Add(self.show_pairing_button,0,wx.ALL,5)
        button_sizer.Add(self.print_button,0,wx.ALL,5)

        parent_sizer.Add(button_sizer,0,wx.EXPAND)

    def create_output_window(self,parent_sizer):
        self.output_window = wx.TextCtrl(self,style=wx.TE_MULTILINE,size=(640,480))

        fixed_font = wx.Font(12,wx.MODERN,wx.NORMAL,wx.NORMAL)
        self.output_window.SetFont(fixed_font)

        parent_sizer.Add(self.output_window,0,wx.ALL|wx.EXPAND,5)

    def show_standings(self,event):
        ''' Output standings as a string '''
        output_text = "Place \tPlayer Name \tRating \tMP \tVP \tVP% \n"
        output_text += "===================================================\n"

        output_text += self.player_list_data.player_standing_list(self.pairing_list_data.current_round)
        self.output_window.SetValue(output_text)

    def show_crosstable(self,event):
        ''' Output crosstable as a string '''
        
        output_text = "Place \tPlayer Name \tRating \t"
        for i in range(self.pairing_list_data.current_round):
            output_text += str(i+1)+"\t"
        output_text += "MP \tVP \tVP% \n"
        output_text += "===================================================\n"

        output_text += self.player_list_data.player_crosstable_list(self.pairing_list_data.current_round)
        print_output = make_printer_text(output_text)
        self.output_window.SetValue(print_output)

    def show_pairings(self,event):
        ''' Output Pairings for current round as a string '''
        header_text = "Parings for Round: "+str(self.pairing_list_data.current_round)+"\n"
        output_text = "Board \tPlayer \tCurrent Score \tMP \tVP\n"
        output_text += "=====================================================\n"

        round_pairings = self.pairing_list_data.GetRoundPairingList(self.pairing_list_data.current_round)
        if len(round_pairings) > 0:
            current_board = round_pairings[0][0]

            for pairing in round_pairings:
                if pairing[0] != current_board:
                    output_text += "=====================================================\n"
                    current_board = pairing[0]
                output_text += str(pairing[0])+"\t"+pairing[1]+"\t"+str(pairing[2])+"\t .... \t ... \n"
        print_output = make_printer_text(output_text)
        display_text = header_text+print_output
        self.output_window.SetValue(display_text)

    def on_print(self,event):
        ''' Print the current output view '''
        pdata = wx.PrintData()
        pdata.SetPaperId(wx.PAPER_A4)
        pdata.SetOrientation(wx.PORTRAIT)
        margins = (wx.Point(15,15),wx.Point(15,15))
        
        data = wx.PrintDialogData(pdata)
        printer = wx.Printer(data)
        text = self.output_window.GetValue()
        printout = TextPrintout(text,"Py Pairing 1.0", margins)
        useSetupDialog = True
        if not printer.Print(self, printout, useSetupDialog) and printer.GetLastError() == wx.PRINTER_ERROR:
            wx.MessageBox("Problem with printer","Printing Error",wx.OK)
        else:
            data = printer.GetPrintDialogData()
            pdata = wx.PrintData(data.GetPrintData())
        printout.Destroy()

class TournamentDetailsDialog(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self,None,-1,'Tournament Details',size=(400,600))
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)

        t_name_label = wx.StaticText(self,-1,"Tournament Name")
        place_label = wx.StaticText(self,-1,"Place")
        begin_date_label = wx.StaticText(self,-1,"Begin Date")
        end_date_label = wx.StaticText(self,-1,"End Date")
        rounds_label = wx.StaticText(self,-1,"Rounds")
        director_label = wx.StaticText(self,-1,"Director")

        self.t_name_txt = wx.TextCtrl(self)
        self.place_txt = wx.TextCtrl(self)
        self.begin_date = wx.DatePickerCtrl(self)
        self.end_date = wx.DatePickerCtrl(self)
        self.rounds_num = wx.TextCtrl(self)
        self.director_txt = wx.TextCtrl(self)

        sizer_1 = wx.FlexGridSizer(2,2,5,5)
        sizer_1.Add(t_name_label,0,wx.ALIGN_LEFT)
        sizer_1.Add(place_label,0,wx.ALIGN_LEFT)
        sizer_1.Add(self.t_name_txt,0,wx.EXPAND)
        sizer_1.Add(self.place_txt,0,wx.EXPAND)

        sizer_2 = wx.FlexGridSizer(2,4,5,5)
        sizer_2.Add(begin_date_label,wx.ALIGN_LEFT)
        sizer_2.Add(end_date_label,wx.ALIGN_LEFT)
        sizer_2.Add(rounds_label,wx.ALIGN_LEFT)
        sizer_2.Add(director_label,wx.ALIGN_LEFT)
        sizer_2.Add(self.begin_date,wx.EXPAND)
        sizer_2.Add(self.end_date,wx.EXPAND)
        sizer_2.Add(self.rounds_num,wx.EXPAND)
        sizer_2.Add(self.director_txt,wx.EXPAND)
        
        

        okay_btn = wx.Button(self,wx.ID_OK)
        okay_btn.SetDefault()
        cancel_btn = wx.Button(self,wx.ID_CANCEL)

        btns = wx.StdDialogButtonSizer()
        btns.Add(okay_btn)
        btns.Add(cancel_btn)
        btns.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(sizer_1,0,wx.ALL,5)
        sizer.Add(sizer_2,0,wx.ALL,5)
        sizer.Add(btns,0,wx.ALL,5)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def get_values(self):
        return (self.t_name_txt.GetValue(),self.place_txt.GetValue(),self.begin_date.GetValue(),
                self.end_date.GetValue(),self.rounds_num.GetValue(),self.director_txt.GetValue())

    def set_values(self,details):
        self.t_name_txt.SetValue(details[0])
        self.place_txt.SetValue(details[1])
        self.begin_date.SetValue(get_DateTime(details[2]))
        self.end_date.SetValue(get_DateTime(details[3]))
        self.rounds_num.SetValue(details[4])
        self.director_txt.SetValue(details[5])
        

class PlayerAvailibilityDialog(wx.Dialog):
    def __init__(self,player):
        wx.Dialog.__init__(self,None,-1,'Player Availibilty',size=(400,600))
        self.locale = wx.Locale(wx.LANGUAGE_ENGLISH)

        total_rounds = 7

        player_string = "ID="+str(player.pairing_id)+":"+player.name
        self.title_text = wx.StaticText(self, -1, player_string)

        checkSizer = wx.BoxSizer(wx.VERTICAL)
        self.checkboxes = []
        for i in range(total_rounds):
            self.checkboxes.append(wx.CheckBox(self,-1,str(i+1)))
            self.checkboxes[i].SetValue(player.availibility[i])
            checkSizer.Add(self.checkboxes[i],0,wx.ALL,5)

        okay_btn = wx.Button(self,wx.ID_OK)
        okay_btn.SetDefault()
        cancel_btn = wx.Button(self,wx.ID_CANCEL)

        btns = wx.StdDialogButtonSizer()
        btns.Add(okay_btn)
        btns.Add(cancel_btn)
        btns.Realize()

        dialog_sizer = wx.BoxSizer(wx.VERTICAL)

        dialog_sizer.Add(self.title_text,0,wx.ALL,5)
        dialog_sizer.Add(checkSizer,0,wx.ALL,5)
        dialog_sizer.Add(btns,0,wx.ALL,5)

        self.SetSizer(dialog_sizer)
        dialog_sizer.Fit(self)

class ModifyPairingDialog(wx.Dialog):
    def __init__(self,pairings):
        wx.Dialog.__init__(self,None,-1,"Manual Pairing",size=(640,720),style=wx.RESIZE_BORDER)

        self.pairings = pairings
        current_round = self.pairings.current_round
        self.draft_pairings = copy.deepcopy(self.pairings.tournament_pairings[current_round-1])
        ''' Start with sizers this time '''

        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        pairing_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.pairing_list = PairingListControl(self)
        self.fill_pairing_ctrl()

        pairing_sizer.Add(self.pairing_list,1,wx.EXPAND)

        unpair_sizer = wx.BoxSizer(wx.VERTICAL)
        boardnum_sizer = wx.BoxSizer(wx.HORIZONTAL)

        board_num_label = wx.StaticText(self,-1,"Board Number:")
        self.board_num = wx.TextCtrl(self)
        player_num_label = wx.StaticText(self,-1,"Player ID:")
        self.player_num = wx.TextCtrl(self)

        boardnum_sizer.Add(board_num_label,0,wx.ALIGN_LEFT)
        boardnum_sizer.Add(self.board_num,0,wx.ALIGN_LEFT)
        boardnum_sizer.Add(player_num_label,0,wx.ALIGN_LEFT)
        boardnum_sizer.Add(self.player_num,0,wx.ALIGN_LEFT)

        self.unpaired_list = UnpairedListControl(self)

        add_btn = wx.Button(self,-1,"Add Player")
        self.Bind(wx.EVT_BUTTON,self.return_player,add_btn)
        delete_btn = wx.Button(self,-1,"Remove Player")
        self.Bind(wx.EVT_BUTTON,self.remove_player,delete_btn)

        btns = wx.StdDialogButtonSizer()
        btns.Add(add_btn)
        btns.Add(delete_btn)
        btns.Realize()

        unpair_sizer.Add(boardnum_sizer,1,wx.EXPAND)
        unpair_sizer.Add(self.unpaired_list,0,wx.EXPAND)
        unpair_sizer.Add(btns,0,wx.EXPAND)

        pairing_sizer.Add(unpair_sizer,1,wx.EXPAND)

        done_button = wx.Button(self,-1,"Accept Pairings")
        self.Bind(wx.EVT_BUTTON,self.exit_dialog,done_button)
        cancel_button = wx.Button(self,wx.ID_CANCEL)

        bottom_btns = wx.StdDialogButtonSizer()
        bottom_btns.Add(done_button)
        bottom_btns.Add(cancel_button)
        bottom_btns.Realize()

        dialog_sizer.Add(pairing_sizer,0,wx.ALL|wx.EXPAND,5)
        dialog_sizer.Add(bottom_btns,0,wx.ALL|wx.EXPAND,5)
        self.SetSizer(dialog_sizer)

    def fill_pairing_ctrl(self):
        current_round = self.pairings.current_round
        if current_round > 0:
            self.pairing_list.populate_list(self.draft_pairings)
            
    def fill_unpaired_list(self,player_list):
        
        for players in player_list:
            self.draft_pairings.add_pairing(('X',players.name,0,0,0,players.pairing_id))
            current_pairing = (players.pairing_id,players.name)
            self.unpaired_list.populate_list(current_pairing)

    def remove_player(self,event):
        row = self.pairing_list.GetFirstSelected()
        current_pairing = (self.pairing_list.GetItemText(row,2),self.pairing_list.GetItemText(row,1))
        self.pairing_list.DeleteItem(row)
        self.unpaired_list.populate_list(current_pairing)

    def return_player(self,event):
        board = self.board_num.GetValue()
        player = self.player_num.GetValue()

        row = self.unpaired_list.FindItem(0,player)
        if row > -1:
            new_pairing = (board,self.unpaired_list.GetItemText(row,1),self.unpaired_list.GetItemText(row,0))
            self.unpaired_list.DeleteItem(row)
            self.pairing_list.add_pairing(new_pairing)
            for i in range(len(self.draft_pairings.pairings)):
                if self.draft_pairings.pairings[i][6] == int(player):
                    self.draft_pairings.pairings[i][0] = board
                    break
                    

    def update_pairings(self):
        current_round = self.pairings.current_round - 1
        self.pairings.tournament_pairings[current_round] = self.draft_pairings
            
        
    def get_pairings(self):
        pairings = []
        return self.draft_pairings
    
    def exit_dialog(self,event):
        ''' This will contain some clean up code before shutting '''
        if self.unpaired_list.GetItemCount() > 0:
            Warn(self,"You must pair all players")
            return
        self.update_pairings()
        self.EndModal(wx.OK)

class PairingListControl(wx.ListCtrl):
    def __init__(self,parent):
        super(PairingListControl,self).__init__(parent,style=wx.LC_REPORT)

        self.InsertColumn(0,"Board")
        self.InsertColumn(1,"Player")
        self.InsertColumn(2,"Player ID");

    def populate_list(self,data):
        for pairing in data.pairings:
            self.Append((pairing[0],pairing[1],pairing[6]))

    def add_pairing(self,data):
        self.Append((data[0],data[1],data[2]))

class UnpairedListControl(wx.ListCtrl):
    def __init__(self,parent):
        super(UnpairedListControl,self).__init__(parent,style=wx.LC_REPORT)

        self.InsertColumn(0,"ID")
        self.InsertColumn(1,"Name")

    def populate_list(self,data):
        self.Append((data[0],data[1]))
    
            
        
        
class TournamentClass:
    ''' Contains Tournament Details '''
    def __init__(self):
        self.name = ""
        self.place = ""
        self.begin_date = ""
        self.end_date = ""
        self.total_rounds = 0
        self.director = ""

    def set_details(self,detail_list):
        ''' detail_list contains the event details as a tuple'''
        if not detail_list:
            return

        self.name = detail_list[0]
        self.place = detail_list[1]
        self.begin_date = detail_list[2]
        self.end_date = detail_list[3]
        self.total_rounds = detail_list[4]
        self.director = detail_list[5]

    def get_details(self):
        ''' returns event details as a tuple'''

        return (self.name,self.place,self.begin_date,self.end_date,self.total_rounds,
                self.director)

    def file_output(self):
        ''' Returns the tournament info in a format suitable for
            writing to a file as text'''
        output_txt = self.name+'\n'+self.place+'\n'+self.begin_date
        output_txt += ','+self.end_date+'\n'+self.director
        output_txt += '\n'+str(self.total_rounds)+'\n'

        return output_txt

class PlayerListClass:
    ''' List of players'''
    def __init__(self):
        self.total_players = 0
        self.players = []

    def reset_players(self):
        ''' Reset when loading a new file '''
        self.total_players = 0
        self.players = []

    def new_player(self):
        ''' Adds a new player
            If total rounds > 0 means event has started and this
            players is a late entry. The missing rounds are
            filled in as not played '''
        total_rounds = 0
        if len(self.players) > 0:
            total_rounds = len(self.players[0].results)
            
        player = PlayerClass(self.total_players)
        for i in range(total_rounds):
            player.enter_results(i+1,["X","",0,0,0,0.0])
        self.players.append(player)
        self.total_players += 1            

    def add_player(self,data):
        ''' Used to add players from file input '''
        player = PlayerClass(self.total_players)
        if len(data) > 2:
            player.update_player(data[0],data[1],data[2])
        else:
            player.update_player(data[0],data[1],None)
        self.players.append(player)
        self.total_players += 1

    def remove_player(self,player_no):
        ''' Removes the player_no entry from the player_list '''

        if player_no > len(self.players):
            #off the end of list
            return
        del self.players[player_no]
        self.total_players -= 1
        ''' Update pairing ID's '''
        for i in range(len(self.players)):
            self.players[i].pairing_id = i

    def delete_round(self):
        ''' Goes through each player and drops the last round of their results
            Used in conjuction with deleteing the last set of pairings '''
        for player in self.players:
            player.results.pop()

    def file_output(self):
        ''' Returns the player list in a format suitable for
            writing to a text file '''

        output_txt = "Name;Rating\n"
        for player in self.players:
            if player.name != '':
                output_txt += player.name+";"+str(player.rating)+";"
                for availibility in player.availibility:
                    if availibility:
                        output_txt += '1'
                    else:
                        output_txt += '0'
                output_txt += '\n'
        output_txt += "\n"

        return output_txt

    def file_pairing_output(self):
        ''' returns the pairings of each player in a format suitable
            for writing to a text file '''

        output_text = "Player_id     Rd1_board;Rd1_mp;Rd1_vp; ....\n"
        for player in self.players:
            if player.name != '':
                output_text += str(player.pairing_id)+" "
                for result in player.results:
                    output_text += str(result.table_no)+";"
                    output_text += str(result.score)+";"
                    output_text += str(result.vp_score)+" "
                output_text += "\n"

        output_text += "\n"
        return output_text

    def player_standing_list(self,round_num):
        ''' Returns a standings list after round_num rounds '''
        output_text = ''
        standing_list = []
        for player in self.players:
            player_score = player.get_player_score_n(round_num)
            if player_score[2] != 0:
                player_percent = float(player_score[1])/float(player_score[2])
            else:
                player_percent = 0.0
            standing_list.append([player.name,player.rating,player_score[0],player_score[1],player_percent])

        standing_list.sort(key = lambda x: (x[2],x[3],x[4]),reverse=True)

        for i in range(len(standing_list)):
            output_text += str(i+1)+"\t"+standing_list[i][0]+"\t"+str(standing_list[i][1])+"\t"
            output_text += str(standing_list[i][2])+"\t"+str(standing_list[i][3])+"\t"
            output_text += '{:.2%}'.format(standing_list[i][4])+"\n"

        return output_text

    def player_crosstable_list(self,round_num):
        ''' Returns a crosstable list after round_num rounds'''
        output_text = ''
        standing_list = []
        for player in self.players:
            player_score = player.get_player_score_n(round_num)
            if player_score[2] != 0:
                player_percent = float(player_score[1])/float(player_score[2])
            else:
                player_percent = 0.0
            standing_list.append([player.pairing_id,player.name,player.rating,player_score[0],player_score[1],player_percent])

        standing_list.sort(key = lambda x: (x[3],x[4],x[5]),reverse=True)

        for i in range(len(standing_list)):
            output_text += str(i+1)+"\t"+standing_list[i][1]+"\t"+str(standing_list[i][2])+"\t"
            for j in range(round_num):
                round_result = self.players[standing_list[i][0]].get_round_result(j)
                output_text += str(round_result[0])+" "+str(round_result[1])+"-"+str(round_result[2])+" "+str(round_result[3])+"\t"

            output_text += str(standing_list[i][3])+"\t"+str(standing_list[i][4])+"\t"+'{:.2%}'.format(standing_list[i][5])+"\n"
        return output_text
        
                
    def player_csv(self):
        output_string = ""
        for player in self.players:
            output_string += player.output_csv()
            
        return output_string
        
class PlayerClass:
    ''' Player Details '''
    def __init__(self,new_id):
        self.pairing_id = new_id
        self.name = ""
        self.rating = 0
        self.results = []
        self.availibility = []
        for i in range(12):
            self.availibility.append(True)
        

    def update_player(self,name,rating,available):
        self.name = name
        self.rating = int(rating)
        if available is not None:
            self.availibility = []
            for i in range(len(available)):
                if available[i] == "1":
                    self.availibility.append(True)
                else:
                    self.availibility.append(False)

    def get_value_n(self,col_number):
        if col_number == 0:
            return self.name
        elif col_number == 1:
            return self.rating
        else:
            return None

    def set_value_n(self,col_number,value):
        if col_number == 0:
            self.name = value
        elif col_number == 1:
            self.rating = num(value)

    def enter_results(self,round_no,score_info):
        if round_no > len(self.results):
            '''Assume we adding a new round '''
            self.results.append(ResultClass())
        # Otherwise just update entry
        score_data = (round_no,score_info[0],score_info[3],score_info[4],0)
        self.results[round_no-1].update_scores(score_data)

    def get_player_score_n(self,round_no):
        ''' Returns the players score as a tuple '''
        score_total = 0
        vp_total = 0
        vp_total_total = 0
        for i in range(round_no):
            score_total += self.results[i].score
            vp_total += self.results[i].vp_score
            vp_total_total += self.results[i].vp_total

        return (score_total,vp_total,vp_total_total)

    def get_round_result(self,round_no):
        return (self.results[round_no].table_no,self.results[round_no].score,
                self.results[round_no].vp_score,self.results[round_no].vp_total)

    def get_player_score(self):
        return self.get_player_score_n(len(self.results))
    
    def output_csv(self):
        output_string = str(self.pairing_id)+","+self.name+","+str(self.rating)+","
        for result in self.results:
            output_string += str(result.table_no)+","+str(result.score)+","+str(result.vp_score)+","
            
        output_string += "\n"
        
        return output_string
    

class ResultClass:
    ''' Results for each player per round
        Consists of Round No, Table Number, Score, VP, VP Total
        Should be in order of rounds (ie first element is round 1 results etc) '''

    def __init__(self):
        self.round_no = 0
        self.table_no = 0
        self.score = 0
        self.vp_score = 0
        self.vp_total = 0.0

    def update_scores(self,score_info):
        self.round_no = score_info[0]
        self.table_no = score_info[1]
        self.score = num(score_info[2])
        self.vp_score = num(score_info[3])
        self.vp_total = num(score_info[4])        

    

class PairingListClass:
    ''' A set of pairings for the tournament'''
    def __init__(self):
        self.current_round = 0
        self.total_rounds = 0
        self.tournament_pairings = []

    def clear_entries(self):
        self.current_round = 0
        self.total_rounds = 0
        self.tournament_pairings = []

    def new_round(self):
        #Creates a new round
        self.total_rounds += 1
        self.tournament_pairings.append(RoundPairingListClass(self.total_rounds))

    def delete_round(self):
        ''' Deletes the most recent round
            Normally used if round was paired in error
            Only delete final round'''
        if self.current_round != self.total_rounds:
            return False
        if len(self.tournament_pairings) == 0:
            return False

        self.tournament_pairings.pop()
        self.current_round -= 1
        self.total_rounds -=1
        
        return True

    def add_pairing(self,round_num,pairing_list):
        if not self.tournament_pairings[round_num]:
            return

        for pairing in pairing_list:
            self.tournament_pairings[round_num].add_pairing(pairing)

        self.tournament_pairings[round_num].sort_table()
        
    def update_names(self,player_id,player_name):
        for round_pairing in self.tournament_pairings:
            for board_pairing in round_pairing.pairings:
                if board_pairing[6] == player_id:
                    board_pairing[1] = player_name
            

    def load_pairing(self,round_num,pairing):
        ''' Adds a single pairing to the pairing list for each round'''
        
        if round_num > self.total_rounds:
            self.tournament_pairings.append(RoundPairingListClass(round_num))
            self.total_rounds += 1
        self.tournament_pairings[round_num-1].add_pairing(pairing)

    def sort_pairings(self):
        for pairing_list in self.tournament_pairings:
            pairing_list.sort_table()

    def list_pairings_round(self,round_num):
        output_txt = ''
        if round_num > self.total_rounds:
            return output_txt

        output_text += "Pairings for Round: "+round_num+"\n"
        return output_txt

    def current_pairing_total(self):
        if self.current_round == 0:
            return 0
        return len(self.tournament_pairings[self.current_round-1].pairings)

    def GetCurrentPairingList(self):
        if self.current_round == 0:
            return []
        return self.tournament_pairings[self.current_round-1].pairings

    def GetRoundPairingList(self,round_num):
        if round_num == 0:
            return []
        return self.tournament_pairings[round_num-1].pairings

    def calc_round_totals(self):
        for round_pairing in self.tournament_pairings:
            round_pairing.calc_board_totals()
                
        
class RoundPairingListClass:
    ''' A set of pairings for each round '''
    def __init__(self,round_number):
        self.round = round_number
        self.pairings = []
        self.board_totals = []

    def add_pairing(self,pairing):
        ''' parameter pairing is a list containing
            board_no,player name, player score, round score, round vp, board_vp, player_id '''
        self.pairings.append(pairing)

    def set_value_n(self,row,col,value):
        self.pairings[row][col]=value

    def sort_table(self):
        self.pairings.sort(key = lambda x:(x[0],-x[2]))

    def calc_board_totals(self):
        ''' Adds up the vp total for each board '''
        vp_totals = {}
        self.board_totals = []
        for pairing in self.pairings:
            if pairing[0] != 'X':
                ''' ignore unpaired players '''
                if vp_totals.has_key(pairing[0]):
                    vp_totals[pairing[0]] += num(pairing[4])
                else:
                    vp_totals[pairing[0]] = num(pairing[4])

        for key in sorted(vp_totals):
            self.board_totals.append(vp_totals[key])


            

class SimplePairingClass:
    ''' A class the produces simple pairings '''
    def __init__(self,round_no,data):
        self.round_no = round_no
        self.pairing_data = data

    def available_count(self):
        total = 0
        for pairing in self.pairing_data:
            if pairing[1].availibility[self.round_no]:
                total += 1
                
        return total
        
    def make_pairing(self):
        ''' Returns a list of pairings
            Each pairing should be in the format
            board_no,player_name,player_mp_score,mp_score,vp_score,player_id'''
        if self.round_no == 0:
            return self.first_round_pairings()
        total_players = self.available_count()
        three_player_boards = 4-(total_players % 4) #Number of short boards
        four_player_boards = ((total_players+3) / 4) - three_player_boards
        pairings = []
        self.pairing_data.sort(key=lambda x: (x[2],x[3]), reverse = True)
        print self.pairing_data
        pair_count = 0
        board_count = 1
        if four_player_boards > 0:
            player_limit = 4
        else:
            player_limit = 3
        for i in range(len(self.pairing_data)):
            board = board_count
            if self.pairing_data[i][1].availibility[self.round_no]:
                pairings.append([board,self.pairing_data[i][1].name,
                             self.pairing_data[i][2],0,0,0,self.pairing_data[i][1].pairing_id])
                pair_count +=1
                if pair_count >= player_limit:
                    board_count += 1
                    if board_count > four_player_boards:
                        player_limit += 3
                    else:
                        player_limit += 4
            else:
                pairings.append(['X',self.pairing_data[i][1].name,
                             self.pairing_data[i][2],0,0,0,self.pairing_data[i][1].pairing_id])
        return pairings

    def first_round_pairings(self):
        ''' Different pairings for first round '''
        total_players = self.available_count()
        three_player_boards = 4-(total_players % 4) #Number of short boards
        four_player_boards = ((total_players+3) / 4) - three_player_boards
        print "Boards: ",total_players,three_player_boards,four_player_boards
        pairings = []
        self.pairing_data.sort(key = lambda x:(x[1].rating), reverse = True)
        print self.pairing_data
        table_total = three_player_boards+four_player_boards
        print "Total boards:",table_total
        pair_count = 0
        for i in range(len(self.pairing_data)):
            board = (pair_count%table_total)+1
            if self.pairing_data[i][1].availibility[self.round_no]:
                pairings.append([board,self.pairing_data[i][1].name,self.pairing_data[i][2],0,0,0,self.pairing_data[i][1].pairing_id])
                pair_count += 1
            else:
                pairings.append(['X',self.pairing_data[i][1].name,self.pairing_data[i][2],0,0,0,self.pairing_data[i][1].pairing_id])

        return pairings
            
class TextPrintout(wx.Printout):
    ''' Provides printing support for this app '''
    def __init__(self, text, title, margin):
        wx.Printout.__init__(self,title)
        self.lines = text.split('\n')
        self.margins = margin
        self.numPages = 1

    def HasPage(self,page):
        return page <= self.numPages

    def GetPageInfo(self):
        return (1, self.numPages,1,self.numPages)

    def CalculateScale(self,dc):
        ppiPrinterX, ppiPrinterY = self.GetPPIPrinter()
        ppiScreenX, ppiScreenY = self.GetPPIScreen()
        logscale = float(ppiPrinterX)/float(ppiScreenX)

        pw,ph = self.GetPageSizePixels()
        dw, dh = dc.GetSize()
        scale = logscale * float(dw)/float(pw)
        dc.SetUserScale(scale,scale)

        self.logUnitsMM = float(ppiPrinterX)/(logscale*25.4)

    def CalculateLayout(self,dc):
        topLeft, bottomRight = self.margins
        dw,dh = dc.GetSize()
        self.x1 = topLeft.x * self.logUnitsMM
        self.y1 = topLeft.y * self.logUnitsMM
        self.x2 = dc.DeviceToLogicalXRel(dw) - bottomRight.x * self.logUnitsMM
        self.y2 = dc.DeviceToLogicalYRel(dh) - bottomRight.y * self.logUnitsMM

        self.pageHeight = self.y2 - self.y1 - 2*self.logUnitsMM
        font = wx.Font(FONTSIZE, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.NORMAL)
        dc.SetFont(font)

        self.lineHeight = dc.GetCharHeight()
        self.linesPerPage = int(self.pageHeight/self.lineHeight)

    def OnPrepearePrinting(self):
        dc = self.GetDC()
        self.CalculateScale(dc)
        self.CalculateLayout(dc)
        self.numPages = len(self.lines)/self.linesPerPage
        if len(self.lines) % self.LinesPerPage != 0:
            self.numPages += 1

    def OnPrintPage(self,page):
        dc = self.GetDC()
        self.CalculateScale(dc)
        self.CalculateLayout(dc)
        dc.SetPen(wx.Pen("black",0))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)

        line = (page-1) * self.linesPerPage
        x = self.x1 + self.logUnitsMM
        y = self.y1 + self.logUnitsMM

        while line < (page * self.linesPerPage):
            dc.DrawText(self.lines[line],x,y)
            y += self.lineHeight
            line += 1
            if line >= len(self.lines):
                break
        return True

class HelpFrameClass(wx.Frame):
    helpText = ''' <h2> PyPairing Help Page </h2>
    <h3> A brief help page for PyPairing 1.0 </h3>
    <b> Introduction</b><p>
    PyPairing is a program designed for the management of multi player games.
    It manage player lists, keeps track of reults and produces pairings for each round
    It is designed for euro style boardgames, where players score both Match Points (MP) and Victory Points (VP)<p>
    <h3> Menu Description</h3><p>
    <h4> File Menu </h4><p>
    1. New Tournament<p>
    New tournament allows you to enter the settings of a newly created event. A dialog box will ask you for the
    Tournament Name, Tournament Venue, Date od start and finish, Number of rounds, and Name of tounament director. <p>
    <b>** Warning:</b> Creating a new event (by entering data and clicking OK) will earse the current event, so make sure you
    save the current event first <p>
    2. Open Tournament <p>
    Load an existing tournament from an aps (Abstract Pairing System) file. Overwrites current event<p>
    3. Save Tournament <p>
    Writes the data from a current event to an aps file<p>
    4. Modify Current Tournament <p>
    Allows you to change the tournament settings (Name, number of rounds etc). Does not effect the data for the current event<p>

    <h4> Standings Menu </h4><p>
    1. Standings<p>
    Shows the players in standing order. The order for standings is Total Match Points, Total Victory Points,
    Percentage of Victory Points against Total Victory Points for each board played<p>
    2. Crosstable<p>
    Shows the round by round results for each player. For each round the crosstable shows Board number, MP, VP and Board VP
    total. Order is the same as Standings order<p>
    3. Pairings<p>
    Shows the pairings for the currently selected round. Ordered by Board number<p>

    <h4> Extras Menu</h4><p>
    1. Delete current round <p>
    If a round has been paired by accident (eg an error is an previous result has been discovered), choosing this will erase
    the most recent round. Note: The most recent round must be the current active round as shown on the pairings page.<p>
    2. Export tournament in csv format<p>
    Exports the tournament data to a file which allows the tournament to be opened in a spreadsheet. <p>

    <h4> Help Menu</h4><p>
    1. Help<p>
    Opens this dialog!<p>
    2. About<p>
    Shows details about program inlcuding contact detail for author (shaunpress@gmail.com)<p>

    <h3> Page Tab Descriptions</h3><p>
    <h4>Player List</h4><p>
    The Player List Page is where you enter and modify player data. For a new tournament this page is blank, while
    for an existing tournament this will contain the list of players.<p>
    <b>Add Player</b><p>
    The Add Player button creates an empty record for a new player. Enter a player name and rating in the respective fields (NB
    The notes field can be left blank and is intended for future use). The rating can either be from a torunament rating system
    or simply decided by the tournament director (it defaults to 0). It is used to provide an initial order for round 1 pairings.
    The data entry is free form so quality control is up to the user<p>
    Players can be "late entered" for the tournament (ie after the first round has been paired).
    Late entered players will be placed on board 'X' and allocated 0 points for each unplayed round (NB this can be modifed later)<p>
    <b>Delete Player</b><p>
    Before the tournament starts a player can be removed from the entry list (eg if they are a duplicate entry, or are unable to attend)
    Cick on the row of the player to be removed and push the Delete Player button. <p>
    NB This option is unavailable after the first round has been paired<p>
    <b>Player Availibility</b><p>
    If a player is unable to play in a particular round, right click on the player concerned. This brings up the
    Player Availibility dialog. Each round that the player will be paired for has a tick. To remove a player from
    the pairings just click on the box (ie untick it) and press OK. The player will then be placed on Board 'X'
    for that round. You are still able to enter a score for that player via the Pairings page if needed. (NB This has no
    effect for previously played rounds)<p>

    <h4>Pairing Page</h4><p>
    The Pairing Page allows you to enter the results for each round, and do pairings for the next round. The page will show
    the pairings for the current round (as signified by the spinner value at the bottom of the page). Results can be entered
    for each player in Match Points and Victory Points Columns. Results are updated when you push the Update button or
    change the current active round.<p>
    <b>Automatic</b><p>
    Produces the pairings for the next round. NB The current active round must be the most recent round of the tournament for this
    option to be available.<p>
    <b>Warning:</b>You can pair the next round before all results of the previous rounds have been entered. If this is done
    by mistake, use the Delete Current Round menu option (under Extras)<p>
    <b>Modify</b><p>
    If there is a need to change an existing pairing, the Modify button will show a dialog to let this happen. The dialog will
    show a set of existing pairings, for the current active round. To modify a pairing, highlight the pairing and choose
    Remove Player. This transfers the player to the right hand list. The enter the Board Number and Player ID for the player and
    choose Add Player to return them to the pairing list. To accept the set of modified pairings push Accept Pairings
    (NB All players must be paired first). If you wish to leave the pairings as they were just choose Cancel<p>
    <b>Update</b><p>
    This button updates the current scores and results. Use it if you want to see standings based on part results. Also use this
    if you are saving the data partway through a round<p>
    <b>Print</b><p>
    Allows you to print the current set of pairings<p>
    <b>Active Round</b><p>
    The Active Round Spinner sets the current round. To pair the next round (or to show current standings) set it to the last paired round.
    To modify results or pairings for previous rounds simply choose a previous round and select the appropriate action<p>

    <h4>Output</h4><p>
    The Output page shows Standings, Crosstables and Pairings (All described in the menu sction). <p>
    <b>Print</b><p>
    Sends the current output view to the printer. Opens a dialog to allow you so select which printer you use<p>
    Note: As the output windows are editable, you can add your own information before printing the content<p>

    <h3>Pairing System</h3><p>
    The pairing system for PyPairing 1.0 is a simple ordered pairing system. For the first round the playsr are sorted in rating
    order and placed on the boards according to the formula Player 1 on board 1, Player 2 on 2, down to board N.
    Then Player N+1 goes on board 1 etc For subsequent rounds the players are ordered by Match Points then Victory Points. The top 4
    players are on board 1, the next 4 on board 2 etc<p>
    Players can play the same opponents more than once.
    If the number of players being paired are not a multiple of 4, the program produces a set of 3 player pairings at the end
    to give every available player a game (ie 3 players left over = 1 3 player board, 2 players = 2 3 player board, 1 player =
    3 3 player boards).
    
    '''
    
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title="Help", size=(400,400))
        html = wx.html.HtmlWindow(self)
        html.SetPage(HelpFrameClass.helpText)
    
        
if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()

    
