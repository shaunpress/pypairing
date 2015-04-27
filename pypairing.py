import wx
import wx.grid

''' Create some Menu Constants '''
ID_NEW_TOURNAMENT = wx.NewId()
ID_SAVE_TOURNAMENT = wx.NewId()
ID_ADD_PLAYER = wx.NewId()
ID_DELETE_PLAYER = wx.NewId()
ID_STANDINGS = wx.NewId()
ID_CROSSTABLE = wx.NewId()
ID_SHOW_PAIRING = wx.NewId()

''' Some general functions to do stuff '''

def get_DateTime(time_string):
    year,month,day = time_string.split('-')
    date = wx.DateTime()
    date.Set(int(day),int(month),int(year))
    return date

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

        self.tournament_details = TournamentClass()
        self.player_details = PlayerListClass()
        self.tournament_pairings = PairingListClass()

        self.view = None

        self.make_menu()
        self.app_page = MyTabFrame(self,self.player_details,self.tournament_pairings)

        self.make_dialogs()


    def make_menu(self):
        menu_bar = wx.MenuBar()

        #File Menu
        file_menu = wx.Menu()
        file_menu.Append(ID_NEW_TOURNAMENT,"New Tournament\tCtrl+N")
        file_menu.Append(wx.ID_OPEN,"Open Tournament\tCtrl+O")
        file_menu.Append(ID_SAVE_TOURNAMENT,"Save Tournament\tCtrl+S")
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT,"Exit\tCtrl+E")
        

        menu_bar.Append(file_menu,"&File")

        #Standings Menue
        standings_menu = wx.Menu()

        menu_bar.Append(standings_menu,"Standings")

        #Extras Menu
        extras_menu = wx.Menu()

        menu_bar.Append(extras_menu,"Extras")

        #Help Menu
        help_menu = wx.Menu()

        menu_bar.Append(help_menu,"Help")

        self.SetMenuBar(menu_bar)
        self.Bind(wx.EVT_MENU,self.OnMenu)

    def make_dialogs(self):
        self.details_dialog = TournamentDetailsDialog()

    def OnMenu(self,event):
        ''' Handle all the menu events in the main frame '''
        evt_id = event.GetId()
        if evt_id == ID_NEW_TOURNAMENT:
            self.modify_tournament()
        elif evt_id == wx.ID_OPEN:
            self.open_tournament()
        elif evt_id == ID_SAVE_TOURNAMENT:
            self.save_tournament()
        elif evt_id == wx.ID_EXIT:
            ret_value = self.exit_app()
            if ret_value:
                self.Destroy()
        else:
            event.Skip()

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
        while lines[line_count] != '':
            pairing_line = lines[line_count].split()
            player_id = int(pairing_line[0])
            for i in range(1,len(pairing_line)):
                info = pairing_line[i].split(";")
                round_data = [info[0],"",player_id,info[1],info[2],0]
                self.player_details.players[player_id].enter_results(i,round_data)
            line_count += 1


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

class PlayerListPage(wx.Panel):
    def __init__(self,parent,data_source):
        super(PlayerListPage,self).__init__(parent)

        #Add the player list grid
        self.player_list_table = PlayerListTable(data_source)
        self.player_grid = wx.grid.Grid(self,size=(640,480))
        self.player_grid.SetTable(self.player_list_table,True)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.player_grid,0,wx.ALL,5)

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

    def add_player_clicked(self,event):
        self.player_list_table.AppendRows()
        msg = wx.grid.GridTableMessage(self.player_list_table,
                                 wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED,1)
        self.player_grid.ProcessTableMessage(msg)

    def delete_player_clicked(self,event):
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
            

        
        
class PlayerListTable(wx.grid.PyGridTableBase):
    def __init__(self,data_source):
        wx.grid.PyGridTableBase.__init__(self)

        self.colLabels = ["Name","Rating","Notes"]
        self.data = data_source

        self.number_of_rows = len(self.data.players)

        self.odd = wx.grid.GridCellAttr()
        self.odd.SetBackgroundColour("sky blue")
        self.odd.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.BOLD))

        self.even = wx.grid.GridCellAttr()
        self.even.SetBackgroundColour("sea green");
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

    def GetAttr(self,row,col, kind):
        attr = [self.even, self.odd][row % 2]
        attr.IncRef()
        return attr

class PairingPage(wx.Panel):
    def __init__(self,parent,data_source):
        super(PairingPage,self).__init__(parent)

        self.pairs_shown = 0
        self.player_details_list = parent.player_list_data
        self.pairing_list_table = PairingListTable(data_source)
        self.pairing_list_grid = wx.grid.Grid(self,size=(640,480))
        self.pairing_list_grid.SetTable(self.pairing_list_table,True)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.pairing_list_grid,0,wx.ALL,5)

        #Add some buttons
        self.auto_btn = wx.Button(self,-1,"Automatic")
        self.Bind(wx.EVT_BUTTON,self.automatic_clicked, self.auto_btn)
        self.modify_btn = wx.Button(self,-1,"Modify")
        self.manual_btn = wx.Button(self,-1,"Manual")
        self.print_btn = wx.Button(self,-1,"Print")
        self.update_btn = wx.Button(self,-1,"Update")
        self.Bind(wx.EVT_BUTTON,self.update_clicked, self.update_btn)

        button_sizer = wx.FlexGridSizer(2,3,5,5)
        button_sizer.Add(self.auto_btn,0,wx.ALL,5)
        button_sizer.Add(self.modify_btn,0,wx.ALL,5)
        button_sizer.Add(self.update_btn,0,wx.ALL,5)
        button_sizer.Add(self.manual_btn,0,wx.ALL,5)
        button_sizer.Add(self.print_btn,0,wx.ALL,5)

        bottom_bar = wx.BoxSizer(wx.HORIZONTAL)
        bottom_bar.Add(button_sizer,0,wx.EXPAND)

        #Add a spinner for rounds

        self.round_spinner = wx.SpinCtrl(self,-1,"",size=(70,70),min=0,max=0,initial=0)
        self.Bind(wx.EVT_SPINCTRL,self.round_changed,self.round_spinner)

        bottom_bar.Add(self.round_spinner,0,wx.RIGHT|wx.EXPAND)

        box.Add(bottom_bar,0,wx.ALL,5)

        self.SetSizer(box)
        self.Layout()

    def automatic_clicked(self,event):
        if self.round_spinner.GetValue() < self.pairing_list_table.data.total_rounds:
            
            #Do not pair for previous rounds
            return
        
        self.pairing_list_table.data.new_round()
        pairing_list = self.make_pairings()
        print pairing_list
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

    def round_changed(self,event):
        new_round = self.round_spinner.GetValue()
        self.pairing_list_table.ChangeCurrentRound(new_round)
        self.update_clicked(event)
        
        
        
    def update_clicked(self,event):
        ''' Update the players data with results from the displayed round
            Called when update button is clicked or when round spinner
            changes '''

        for pairing in self.pairing_list_table.GetCurrentPairings():
            self.player_details_list.players[pairing[6]].enter_results(self.pairing_list_table.current_round,pairing)
            print pairing  
    
        self.show_round_pairings()

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
        # NB This is a dummy pairing function for testing only
        # Destroy later

        pairings = []
        for i in range(len(self.player_details_list.players)):
            board = (i/4+1)
            player_id = i
            score = 16-i
            pairings.append([board,self.player_details_list.players[i].name,player_id,score,0,0,player_id])

        return pairings
            

class PairingListTable(wx.grid.PyGridTableBase):
    def __init__(self,data_source):
        wx.grid.PyGridTableBase.__init__(self)

        self.colLabels = ["Board","Player","Score","Placing","Victory Points"]
        self.data = data_source
        self.current_round = 0

        self.number_of_rows = self.data.current_pairing_total()

        self.odd = wx.grid.GridCellAttr()
        self.odd.SetBackgroundColour("sky blue")
        self.odd.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.BOLD))

        self.even = wx.grid.GridCellAttr()
        self.even.SetBackgroundColour("light blue");
        self.even.SetFont(wx.Font(10,wx.SWISS,wx.NORMAL,wx.BOLD))

    def GetNumberRows(self):
        print self.data.current_pairing_total()
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
        attr.IncRef()
        return attr

    def GetCurrentPairings(self):
        return self.data.GetCurrentPairingList()

    def ChangeCurrentRound(self,new_round):
        self.current_round = new_round
        self.data.current_round = new_round

class OutputPage(wx.Panel):
    def __init__(self,parent):
        super(OutputPage,self).__init__(parent)

        box = wx.BoxSizer(wx.VERTICAL)
        self.create_button_bar(box)

        self.create_output_window(box)

        self.SetSizer(box)
        self.Layout()

    def create_button_bar(self,parent_sizer):
        
        self.standings_button = wx.Button(self,ID_STANDINGS,"Standings")
        self.crosstable_button = wx.Button(self,ID_CROSSTABLE,"Crosstable")
        self.show_pairing_button = wx.Button(self, ID_SHOW_PAIRING,"Pairings")

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.standings_button,0,wx.ALL,5)
        button_sizer.Add(self.crosstable_button,0,wx.ALL,5)
        button_sizer.Add(self.show_pairing_button,0,wx.ALL,5)

        parent_sizer.Add(button_sizer,0,wx.EXPAND)

    def create_output_window(self,parent_sizer):
        self.output_window = wx.TextCtrl(self,style=wx.TE_MULTILINE,size=(640,480))

        parent_sizer.Add(self.output_window,0,wx.ALL,5)

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
        output_txt += '\n'+self.total_rounds+'\n'

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
        player = PlayerClass(self.total_players)
        self.players.append(player)
        self.total_players += 1

    def add_player(self,data):
        ''' Used to add players from file input '''
        player = PlayerClass(self.total_players)
        player.update_player(data[0],data[1])
        self.players.append(player)
        self.total_players += 1

    def remove_player(self,player_no):
        ''' Removes the player_no entry from the player_list '''

        if player_no > len(self.players):
            #off the end of list
            return

        del self.players[player_no]
        self.total_players -= 1

    def file_output(self):
        ''' Returns the player list in a format suitable for
            writing to a text file '''

        output_txt = "Name;Rating\n"
        for player in self.players:
            if player.name != '':
                output_txt += player.name+";"+player.rating+"\n"
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
        print output_text
        return output_text

        
class PlayerClass:
    ''' Player Details '''
    def __init__(self,new_id):
        self.pairing_id = new_id
        self.name = ""
        self.rating = 0
        self.results = []

    def update_player(self,name,rating):
        self.name = name
        self.rating = rating

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
            self.rating = value

    def enter_results(self,round_no,score_info):
        if round_no > len(self.results):
            '''Assume we adding a new round '''
            self.results.append(ResultClass())
        # Otherwise just update entry
        print score_info
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
        self.score = score_info[2]
        self.vp_score = score_info[3]
        self.vp_total = score_info[4]        

    

class PairingListClass:
    ''' A set of pairings for the tournament'''
    def __init__(self):
        self.current_round = 0
        self.total_rounds = 0
        self.tournament_pairings = []

    def new_round(self):
        #Creates a new round
        self.total_rounds += 1
        self.tournament_pairings.append(RoundPairingListClass(self.total_rounds))

    def add_pairing(self,round_num,pairing_list):
        if not self.tournament_pairings[round_num]:
            return

        for pairing in pairing_list:
            self.tournament_pairings[round_num].add_pairing(pairing)

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
                
        
class RoundPairingListClass:
    ''' A set of pairings for each round '''
    def __init__(self,round_number):
        self.round = round_number
        self.pairings = []

    def add_pairing(self,pairing):
        ''' parameter pairing is a list containing
            board_no,player name, player score, round score, round vp '''
        self.pairings.append(pairing)

    def set_value_n(self,row,col,value):
        self.pairings[row][col]=value

        
if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()

    
