import app
import ui
import player
import net
import wndMgr
import messenger
import guild
import chr
import nonplayer
import localeInfo
import constInfo
import uiHealth
import uiToolTip
import item

def HAS_FLAG(value, flag):
	return (value & flag) == flag

class TargetBoard(ui.ThinBoard):
	class InfoBoard(ui.ThinBoard):
		class ItemListBoxItem(ui.ListBoxExNew.Item):
			def __init__(self, width):
				ui.ListBoxExNew.Item.__init__(self)

				image = ui.ExpandedImageBox()
				image.SetParent(self)
				image.Show()
				self.image = image

				nameLine = ui.TextLine()
				nameLine.SetParent(self)
				nameLine.SetPosition(32 + 5, 0)
				nameLine.Show()
				self.nameLine = nameLine

				self.SetSize(width, 32 + 5)

			def LoadImage(self, image, name = None):
				self.image.LoadImage(image)
				self.SetSize(self.GetWidth(), self.image.GetHeight() + 5 * (self.image.GetHeight() / 32))
				if name != None:
					self.SetText(name)

			def SetText(self, text):
				self.nameLine.SetText(text)

			def RefreshHeight(self):
				ui.ListBoxExNew.Item.RefreshHeight(self)
				self.image.SetRenderingRect(0.0, 0.0 - float(self.removeTop) / float(self.GetHeight()), 0.0, 0.0 - float(self.removeBottom) / float(self.GetHeight()))
				self.image.SetPosition(0, - self.removeTop)

		MAX_ITEM_COUNT = 5

		STONE_START_VNUM = 28030
		STONE_LAST_VNUM = 28042

		BOARD_WIDTH = 220

		def __init__(self):
			ui.ThinBoard.__init__(self)

			self.HideCorners(self.LT)
			self.HideCorners(self.RT)
			self.HideLine(self.T)

			self.race = 0
			self.hasItems = False

			self.itemTooltip = uiToolTip.ItemToolTip()
			self.itemTooltip.HideToolTip()

			self.stoneImg = None
			self.stoneVnum = None
			self.lastStoneVnum = 0
			self.nextStoneIconChange = 0

			self.SetSize(self.BOARD_WIDTH, 0)

		def __del__(self):
			ui.ThinBoard.__del__(self)

		def __UpdatePosition(self, targetBoard):
			self.SetPosition(targetBoard.GetLeft() + (targetBoard.GetWidth() - self.GetWidth()) / 2, targetBoard.GetBottom() - 17)

		def Open(self, targetBoard, race):
			self.__LoadInformation(race)

			self.SetSize(self.BOARD_WIDTH, self.yPos + 10)
			self.__UpdatePosition(targetBoard)

			self.Show()

		def Refresh(self):
			self.__LoadInformation(self.race)
			self.SetSize(self.BOARD_WIDTH, self.yPos + 10)

		def Close(self):
			self.itemTooltip.HideToolTip()
			self.Hide()

		def __LoadInformation(self, race):
			self.yPos = 7
			self.children = []
			self.race = race
			self.stoneImg = None
			self.stoneVnum = None
			self.nextStoneIconChange = 0

			self.__LoadInformation_Default(race)
			self.__LoadInformation_Drops(race)

		def __LoadInformation_Default_GetHitRate(self, race):
			attacker_dx = nonplayer.GetMonsterDX(race)
			attacker_level = nonplayer.GetMonsterLevel(race)

			self_dx = player.GetStatus(player.DX)
			self_level = player.GetStatus(player.LEVEL)

			iARSrc = min(90, (attacker_dx * 4 + attacker_level * 2) / 6)
			iERSrc = min(90, (self_dx * 4 + self_level * 2) / 6)

			fAR = (float(iARSrc) + 210.0) / 300.0
			fER = (float(iERSrc) * 2 + 5) / (float(iERSrc) + 95) * 3.0 / 10.0

			return fAR - fER

		def __LoadInformation_Default(self, race):
			self.AppendSeperator()
			self.AppendTextLine("PV: %s" % str(nonplayer.GetMonsterMaxHP(race)))

		def __LoadInformation_Drops(self, race):
			self.AppendSeperator()
			if race in constInfo.MONSTER_INFO_DATA:
				if len(constInfo.MONSTER_INFO_DATA[race]["items"]) == 0:
					self.AppendTextLine("Nu se dropeaza niciun item !")
				else:
					itemListBox = ui.ListBoxExNew(32 + 5, self.MAX_ITEM_COUNT)
					itemListBox.SetSize(self.GetWidth() - 15 * 2 - ui.ScrollBar.SCROLLBAR_WIDTH, (32 + 5) * self.MAX_ITEM_COUNT)
					height = 0
					for curItem in constInfo.MONSTER_INFO_DATA[race]["items"]:
						if curItem.has_key("vnum_list"):
							height += self.AppendItem(itemListBox, curItem["vnum_list"], curItem["count"])
						else:
							height += self.AppendItem(itemListBox, curItem["vnum"], curItem["count"])
					if height < itemListBox.GetHeight():
						itemListBox.SetSize(itemListBox.GetWidth(), height)
					self.AppendWindow(itemListBox, 15)
					itemListBox.SetBasePos(0)

					if len(constInfo.MONSTER_INFO_DATA[race]["items"]) > itemListBox.GetViewItemCount():
						itemScrollBar = ui.ScrollBar()
						itemScrollBar.SetParent(self)
						itemScrollBar.SetPosition(itemListBox.GetRight(), itemListBox.GetTop())
						itemScrollBar.SetScrollBarSize(32 * self.MAX_ITEM_COUNT + 5 * (self.MAX_ITEM_COUNT - 1))
						itemScrollBar.SetMiddleBarSize(float(self.MAX_ITEM_COUNT) / float(height / (32 + 5)))
						itemScrollBar.Show()
						itemListBox.SetScrollBar(itemScrollBar)
			else:
				self.AppendTextLine("Nu se dropeaza niciun item !")

		def AppendTextLine(self, text):
			textLine = ui.TextLine()
			textLine.SetParent(self)
			textLine.SetWindowHorizontalAlignCenter()
			textLine.SetHorizontalAlignCenter()
			textLine.SetText(text)
			textLine.SetPosition(0, self.yPos)
			textLine.Show()

			self.children.append(textLine)
			self.yPos += 17

		def AppendSeperator(self):
			img = ui.ImageBox()
			img.LoadImage("d:/ymir work/ui/seperator.tga")
			self.AppendWindow(img)
			img.SetPosition(img.GetLeft(), img.GetTop() - 15)
			self.yPos -= 15

		def AppendItem(self, listBox, vnums, count):
			if type(vnums) == int:
				vnum = vnums
			else:
				vnum = vnums[0]

			item.SelectItem(vnum)
			itemName = item.GetItemName()
			if type(vnums) != int and len(vnums) > 1:
				vnums = sorted(vnums)
				realName = itemName[:itemName.find("+")]
				if item.GetItemType() == item.ITEM_TYPE_METIN:
					realName = "Ghoststone"
					itemName = realName + "+0 - +4"
				else:
					itemName = realName + "+" + str(vnums[0] % 10) + " - +" + str(vnums[len(vnums) - 1] % 10)
				vnum = vnums[len(vnums) - 1]

			myItem = self.ItemListBoxItem(listBox.GetWidth())
			myItem.LoadImage(item.GetIconImageFileName())
			if count <= 1:
				myItem.SetText(itemName)
			else:
				myItem.SetText("%dx %s" % (count, itemName))
			myItem.SAFE_SetOverInEvent(self.OnShowItemTooltip, vnum)
			myItem.SAFE_SetOverOutEvent(self.OnHideItemTooltip)
			listBox.AppendItem(myItem)

			if item.GetItemType() == item.ITEM_TYPE_METIN:
				self.stoneImg = myItem
				self.stoneVnum = vnums
				self.lastStoneVnum = self.STONE_LAST_VNUM + vnums[len(vnums) - 1] % 1000 / 100 * 100

			return myItem.GetHeight()

		def OnShowItemTooltip(self, vnum):
			item.SelectItem(vnum)
			if item.GetItemType() == item.ITEM_TYPE_METIN:
				self.itemTooltip.isStone = True
				self.itemTooltip.isBook = False
				self.itemTooltip.isBook2 = False
				self.itemTooltip.SetItemToolTip(self.lastStoneVnum)
			else:
				self.itemTooltip.isStone = False
				self.itemTooltip.isBook = True
				self.itemTooltip.isBook2 = True
				self.itemTooltip.SetItemToolTip(vnum)

		def OnHideItemTooltip(self):
			self.itemTooltip.HideToolTip()

		def AppendWindow(self, wnd, x = 0, width = 0, height = 0):
			if width == 0:
				width = wnd.GetWidth()
			if height == 0:
				height = wnd.GetHeight()

			wnd.SetParent(self)
			if x == 0:
				wnd.SetPosition((self.GetWidth() - width) / 2, self.yPos)
			else:
				wnd.SetPosition(x, self.yPos)
			wnd.Show()

			self.children.append(wnd)
			self.yPos += height + 5

		def OnUpdate(self):
			if self.stoneImg != None and self.stoneVnum != None and app.GetTime() >= self.nextStoneIconChange:
				nextImg = self.lastStoneVnum + 1
				if nextImg % 100 > self.STONE_LAST_VNUM % 100:
					nextImg -= (self.STONE_LAST_VNUM - self.STONE_START_VNUM) + 1
				self.lastStoneVnum = nextImg
				self.nextStoneIconChange = app.GetTime() + 2.5

				item.SelectItem(nextImg)
				itemName = item.GetItemName()
				realName = itemName[:itemName.find("+")]
				realName = realName + "+0 - +4"
				self.stoneImg.LoadImage(item.GetIconImageFileName(), realName)

				if self.itemTooltip.IsShow() and self.itemTooltip.isStone:
					self.itemTooltip.SetItemToolTip(nextImg)

	BUTTON_NAME_LIST = ( 
		localeInfo.TARGET_BUTTON_WHISPER, 
		localeInfo.TARGET_BUTTON_EXCHANGE, 
		localeInfo.TARGET_BUTTON_FIGHT, 
		localeInfo.TARGET_BUTTON_ACCEPT_FIGHT, 
		localeInfo.TARGET_BUTTON_AVENGE, 
		localeInfo.TARGET_BUTTON_FRIEND, 
		localeInfo.TARGET_BUTTON_INVITE_PARTY, 
		localeInfo.TARGET_BUTTON_LEAVE_PARTY, 
		localeInfo.TARGET_BUTTON_EXCLUDE, 
		localeInfo.TARGET_BUTTON_INVITE_GUILD,
		localeInfo.TARGET_BUTTON_DISMOUNT,
		localeInfo.TARGET_BUTTON_EXIT_OBSERVER,
		localeInfo.TARGET_BUTTON_VIEW_EQUIPMENT,
		localeInfo.TARGET_BUTTON_REQUEST_ENTER_PARTY,
		localeInfo.TARGET_BUTTON_BUILDING_DESTROY,
		localeInfo.TARGET_BUTTON_EMOTION_ALLOW,
		"VOTE_BLOCK_CHAT",
	)

	GRADE_NAME =	{
						nonplayer.PAWN : localeInfo.TARGET_LEVEL_PAWN,
						nonplayer.S_PAWN : localeInfo.TARGET_LEVEL_S_PAWN,
						nonplayer.KNIGHT : localeInfo.TARGET_LEVEL_KNIGHT,
						nonplayer.S_KNIGHT : localeInfo.TARGET_LEVEL_S_KNIGHT,
						nonplayer.BOSS : localeInfo.TARGET_LEVEL_BOSS,
						nonplayer.KING : localeInfo.TARGET_LEVEL_KING,
					}
	EXCHANGE_LIMIT_RANGE = 3000

	def __init__(self):
		ui.ThinBoard.__init__(self)
		self.SaveSecond = 0
		
		self.HPText = ui.TextLine()
		self.HPText.SetParent(self)
		self.HPText.SetDefaultFontName()
		self.HPText.SetOutline()
		self.HPText.SetPosition(30, 23)
		self.HPText.Hide()

		name = ui.TextLine()
		pGauge = ui.Gauge()
		name.SetParent(self)
		name.SetDefaultFontName()
		name.SetOutline()
		name.Show()

		hpGauge = ui.Gauge()
		hpGauge.SetParent(self)
		hpGauge.MakeGauge(130, "red")
		hpGauge.Hide()
		
		hpPercenttxt = ui.TextLine()
		hpPercenttxt.SetParent(self)
		hpPercenttxt.SetPosition(160, 13)
		hpPercenttxt.SetText("")
		hpPercenttxt.Hide()

		closeButton = ui.Button()
		closeButton.SetParent(self)
		closeButton.SetUpVisual("d:/ymir work/ui/public/close_button_01.sub")
		closeButton.SetOverVisual("d:/ymir work/ui/public/close_button_02.sub")
		closeButton.SetDownVisual("d:/ymir work/ui/public/close_button_03.sub")
		closeButton.SetPosition(30, 13)

		if localeInfo.IsARABIC():
			hpGauge.SetPosition(55, 17)
			hpGauge.SetWindowHorizontalAlignLeft()
			closeButton.SetWindowHorizontalAlignLeft()
		else:
			hpGauge.SetPosition(175, 17)
			hpGauge.SetWindowHorizontalAlignRight()
			closeButton.SetWindowHorizontalAlignRight()

		infoButton = ui.Button()
		infoButton.SetParent(self)
		infoButton.SetUpVisual("d:/ymir work/ui/pattern/q_mark_01.tga")
		infoButton.SetOverVisual("d:/ymir work/ui/pattern/q_mark_02.tga")
		infoButton.SetDownVisual("d:/ymir work/ui/pattern/q_mark_01.tga")
		infoButton.SetEvent(ui.__mem_func__(self.OnPressedInfoButton))
		infoButton.Hide()

		infoBoard = self.InfoBoard()
		infoBoard.Hide()
		infoButton.showWnd = infoBoard

		closeButton.SetEvent(ui.__mem_func__(self.OnPressedCloseButton))
		closeButton.Show()

		self.buttonDict = {}
		self.showingButtonList = []
		for buttonName in self.BUTTON_NAME_LIST:
			button = ui.Button()
			button.SetParent(self)
		
			if localeInfo.IsARABIC():
				button.SetUpVisual("d:/ymir work/ui/public/Small_Button_01.sub")
				button.SetOverVisual("d:/ymir work/ui/public/Small_Button_02.sub")
				button.SetDownVisual("d:/ymir work/ui/public/Small_Button_03.sub")
			else:
				button.SetUpVisual("d:/ymir work/ui/public/small_thin_button_01.sub")
				button.SetOverVisual("d:/ymir work/ui/public/small_thin_button_02.sub")
				button.SetDownVisual("d:/ymir work/ui/public/small_thin_button_03.sub")
			
			button.SetWindowHorizontalAlignCenter()
			button.SetText(buttonName)
			button.Hide()
			self.buttonDict[buttonName] = button
			self.showingButtonList.append(button)

		self.buttonDict[localeInfo.TARGET_BUTTON_WHISPER].SetEvent(ui.__mem_func__(self.OnWhisper))
		self.buttonDict[localeInfo.TARGET_BUTTON_EXCHANGE].SetEvent(ui.__mem_func__(self.OnExchange))
		self.buttonDict[localeInfo.TARGET_BUTTON_FIGHT].SetEvent(ui.__mem_func__(self.OnPVP))
		self.buttonDict[localeInfo.TARGET_BUTTON_ACCEPT_FIGHT].SetEvent(ui.__mem_func__(self.OnPVP))
		self.buttonDict[localeInfo.TARGET_BUTTON_AVENGE].SetEvent(ui.__mem_func__(self.OnPVP))
		self.buttonDict[localeInfo.TARGET_BUTTON_FRIEND].SetEvent(ui.__mem_func__(self.OnAppendToMessenger))
		self.buttonDict[localeInfo.TARGET_BUTTON_FRIEND].SetEvent(ui.__mem_func__(self.OnAppendToMessenger))
		self.buttonDict[localeInfo.TARGET_BUTTON_INVITE_PARTY].SetEvent(ui.__mem_func__(self.OnPartyInvite))
		self.buttonDict[localeInfo.TARGET_BUTTON_LEAVE_PARTY].SetEvent(ui.__mem_func__(self.OnPartyExit))
		self.buttonDict[localeInfo.TARGET_BUTTON_EXCLUDE].SetEvent(ui.__mem_func__(self.OnPartyRemove))

		self.buttonDict[localeInfo.TARGET_BUTTON_INVITE_GUILD].SAFE_SetEvent(self.__OnGuildAddMember)
		self.buttonDict[localeInfo.TARGET_BUTTON_DISMOUNT].SAFE_SetEvent(self.__OnDismount)
		self.buttonDict[localeInfo.TARGET_BUTTON_EXIT_OBSERVER].SAFE_SetEvent(self.__OnExitObserver)
		self.buttonDict[localeInfo.TARGET_BUTTON_VIEW_EQUIPMENT].SAFE_SetEvent(self.__OnViewEquipment)
		self.buttonDict[localeInfo.TARGET_BUTTON_REQUEST_ENTER_PARTY].SAFE_SetEvent(self.__OnRequestParty)
		self.buttonDict[localeInfo.TARGET_BUTTON_BUILDING_DESTROY].SAFE_SetEvent(self.__OnDestroyBuilding)
		self.buttonDict[localeInfo.TARGET_BUTTON_EMOTION_ALLOW].SAFE_SetEvent(self.__OnEmotionAllow)
		
		self.buttonDict["VOTE_BLOCK_CHAT"].SetEvent(ui.__mem_func__(self.__OnVoteBlockChat))

		self.name = name
		self.hpGauge = hpGauge
		self.infoButton = infoButton
		self.vnum = 0
		self.hpPercenttxt = hpPercenttxt
		self.closeButton = closeButton
		self.nameString = 0
		self.nameLength = 0
		self.vid = 0
		self.eventWhisper = None
		self.isShowButton = FALSE

		self.__Initialize()
		self.ResetTargetBoard()
		self.healthBoard = uiHealth.HealthBoard()

	def __del__(self):
		ui.ThinBoard.__del__(self)

		print "===================================================== DESTROYED TARGET BOARD"

	def __Initialize(self):
		self.nameString = ""
		self.nameLength = 0
		self.vid = 0
		self.vnum = 0
		self.isShowButton = FALSE

	def Destroy(self):
		self.eventWhisper = None
		self.infoButton = None
		self.closeButton = None
		self.showingButtonList = None
		self.buttonDict = None
		self.name = None
		self.hpGauge = None
		self.hpPercenttxt = None
		self.__Initialize()

	def RefreshMonsterInfoBoard(self):
		if not self.infoButton.showWnd.IsShow():
			return

		self.infoButton.showWnd.Refresh()

	def OnPressedInfoButton(self):
		net.SendTargetInfoLoad(player.GetTargetVID())
		if self.infoButton.showWnd.IsShow():
			self.infoButton.showWnd.Close()
		elif self.vnum != 0:
			self.infoButton.showWnd.Open(self, self.vnum)

	def OnPressedCloseButton(self):
		player.ClearTarget()
		self.Close()

	def Close(self):
		self.__Initialize()
		self.infoButton.showWnd.Close()
		self.healthBoard.Hide()
		self.Hide()

	def Open(self, vid, name):
		if vid:
			if not constInfo.GET_VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD():
				if not player.IsSameEmpire(vid):
					self.Hide()
					return

			if vid != self.GetTargetVID():
				self.ResetTargetBoard()
				self.SetTargetVID(vid)
				self.SetTargetName(name)

			if player.IsMainCharacterIndex(vid):
				self.__ShowMainCharacterMenu()		
			elif chr.INSTANCE_TYPE_BUILDING == chr.GetInstanceType(self.vid):
				self.Hide()
			else:
				self.RefreshButton()
				self.Show()
		else:
			self.HideAllButton()
			self.__ShowButton(localeInfo.TARGET_BUTTON_WHISPER)
			self.__ShowButton("VOTE_BLOCK_CHAT")
			self.__ArrangeButtonPosition()
			self.SetTargetName(name)
			self.Show()
			
	def Refresh(self):
		if self.IsShow():
			if self.IsShowButton():			
				self.RefreshButton()		

	def RefreshByVID(self, vid):
		if vid == self.GetTargetVID():			
			self.Refresh()
			
	def RefreshByName(self, name):
		if name == self.GetTargetName():
			self.Refresh()

	def __ShowMainCharacterMenu(self):
		canShow=0

		self.HideAllButton()

		if player.IsMountingHorse():
			self.__ShowButton(localeInfo.TARGET_BUTTON_DISMOUNT)
			canShow=1

		if player.IsObserverMode():
			self.__ShowButton(localeInfo.TARGET_BUTTON_EXIT_OBSERVER)
			canShow=1

		if canShow:
			self.__ArrangeButtonPosition()
			self.Show()
		else:
			self.Hide()
			
	def __ShowNameOnlyMenu(self):
		self.HideAllButton()

	def SetWhisperEvent(self, event):
		self.eventWhisper = event

	def UpdatePosition(self):
		self.SetPosition(wndMgr.GetScreenWidth()/2 - self.GetWidth()/2, 10)

	def ResetTargetBoard(self):

		for btn in self.buttonDict.values():
			btn.Hide()

		self.__Initialize()

		self.name.SetPosition(0, 13) #0,13 fereastra aia normala,nu are treaba cu duelul
		self.name.SetHorizontalAlignCenter()
		self.name.SetWindowHorizontalAlignCenter()
		self.hpGauge.Hide()
		self.infoButton.Hide()
		self.infoButton.showWnd.Close()
		self.hpPercenttxt.Hide()
		self.SetSize(250, 40) #40 default,la mobi

	def SetTargetVID(self, vid):
		self.vid = vid
		self.vnum = 0

	def SetEnemyVID(self, vid):
		self.SetTargetVID(vid)

		name = chr.GetNameByVID(vid)
		vnum = nonplayer.GetRaceNumByVID(vid)
		level = nonplayer.GetLevelByVID(vid)
		grade = nonplayer.GetGradeByVID(vid)

		nameFront = ""
		if -1 != level:
			nameFront += "Lv." + str(level) + " "
		if self.GRADE_NAME.has_key(grade):
			nameFront += "(" + self.GRADE_NAME[grade] + ") "

		self.SetTargetName(nameFront + name)
		(textWidth, textHeight) = self.name.GetTextSize()

		self.infoButton.SetPosition(textWidth + 25, 12)
		self.infoButton.SetWindowHorizontalAlignLeft()

		self.vnum = vnum
		self.infoButton.Show()

	def GetTargetVID(self):
		return self.vid

	def GetTargetName(self):
		return self.nameString

	def SetTargetName(self, name):
		self.nameString = name
		self.nameLength = len(name)
		self.name.SetText(name)

	def SetHP(self, hpPercentage):
		if not self.hpGauge.IsShow():

			self.SetSize(200 + 7*self.nameLength, self.GetHeight())#200default la inceput

			self.name.SetPosition(23, 13) #23 and 13////23 e sus jos,scazi nr,urca el!!

			self.name.SetWindowHorizontalAlignLeft()
			self.name.SetHorizontalAlignLeft()
			self.hpGauge.Show()
			self.UpdatePosition()
			self.hpPercenttxt.SetPosition(200 + 7*self.nameLength-205, 13) #percent mobi pozitionare
			self.hpPercenttxt.Show()
			if player.IsPVPInstance(self.vid):
				self.hpPercenttxt.Hide()

		self.hpGauge.SetPercentage(hpPercentage, 100)
		self.hpPercenttxt.SetText("%d%%" % (hpPercentage))

	def ShowDefaultButton(self):

		self.isShowButton = TRUE
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_WHISPER])
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_EXCHANGE])
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_FIGHT])
		self.showingButtonList.append(self.buttonDict[localeInfo.TARGET_BUTTON_EMOTION_ALLOW])
		for button in self.showingButtonList:
			button.Show()

	def HideAllButton(self):
		self.isShowButton = FALSE
		for button in self.showingButtonList:
			button.Hide()
		self.showingButtonList = []

	def __ShowButton(self, name):

		if not self.buttonDict.has_key(name):
			return

		self.buttonDict[name].Show()
		self.showingButtonList.append(self.buttonDict[name])

	def __HideButton(self, name):

		if not self.buttonDict.has_key(name):
			return

		button = self.buttonDict[name]
		button.Hide()

		for btnInList in self.showingButtonList:
			if btnInList == button:
				self.showingButtonList.remove(button)
				break

	def OnWhisper(self):
		if None != self.eventWhisper:
			self.eventWhisper(self.nameString)

	def OnExchange(self):
		net.SendExchangeStartPacket(self.vid)

	def OnPVP(self):
		net.SendChatPacket("/pvp %d" % (self.vid))

	def OnAppendToMessenger(self):
		net.SendMessengerAddByVIDPacket(self.vid)

	def OnPartyInvite(self):
		net.SendPartyInvitePacket(self.vid)

	def OnPartyExit(self):
		net.SendPartyExitPacket()

	def OnPartyRemove(self):
		net.SendPartyRemovePacket(self.vid)

	def __OnGuildAddMember(self):
		net.SendGuildAddMemberPacket(self.vid)

	def __OnDismount(self):
		net.SendChatPacket("/unmount")

	def __OnExitObserver(self):
		net.SendChatPacket("/observer_exit")

	def __OnViewEquipment(self):
		net.SendChatPacket("/view_equip " + str(self.vid))

	def __OnRequestParty(self):
		net.SendChatPacket("/party_request " + str(self.vid))

	def __OnDestroyBuilding(self):
		net.SendChatPacket("/build d %d" % (self.vid))

	def __OnEmotionAllow(self):
		net.SendChatPacket("/emotion_allow %d" % (self.vid))
		
	def __OnVoteBlockChat(self):
		cmd = "/vote_block_chat %s" % (self.nameString)
		net.SendChatPacket(cmd)

	def OnPressEscapeKey(self):
		self.OnPressedCloseButton()
		return TRUE

	def IsShowButton(self):
		return self.isShowButton

	def RefreshButton(self):

		self.HideAllButton()

		if chr.INSTANCE_TYPE_BUILDING == chr.GetInstanceType(self.vid):
			#self.__ShowButton(localeInfo.TARGET_BUTTON_BUILDING_DESTROY)
			#self.__ArrangeButtonPosition()
			return
		
		if player.IsPVPInstance(self.vid) or player.IsObserverMode():
			# PVP_INFO_SIZE_BUG_FIX
			self.SetSize(200 + 7*self.nameLength, 40) #200 cica,40 cica
			#self.SetSize(200 + 7*self.nameLength, self.GetHeight())#200default la inceput
			self.UpdatePosition()
			# END_OF_PVP_INFO_SIZE_BUG_FIX			
			return	

		self.ShowDefaultButton()

		if guild.MainPlayerHasAuthority(guild.AUTH_ADD_MEMBER):
			if not guild.IsMemberByName(self.nameString):
				if 0 == chr.GetGuildID(self.vid):
					self.__ShowButton(localeInfo.TARGET_BUTTON_INVITE_GUILD)

		if not messenger.IsFriendByName(self.nameString):
			self.__ShowButton(localeInfo.TARGET_BUTTON_FRIEND)

		if player.IsPartyMember(self.vid):

			self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)

			if player.IsPartyLeader(self.vid):
				self.__ShowButton(localeInfo.TARGET_BUTTON_LEAVE_PARTY)
			elif player.IsPartyLeader(player.GetMainCharacterIndex()):
				self.__ShowButton(localeInfo.TARGET_BUTTON_EXCLUDE)

		else:
			if player.IsPartyMember(player.GetMainCharacterIndex()):
				if player.IsPartyLeader(player.GetMainCharacterIndex()):
					self.__ShowButton(localeInfo.TARGET_BUTTON_INVITE_PARTY)
			else:
				if chr.IsPartyMember(self.vid):
					self.__ShowButton(localeInfo.TARGET_BUTTON_REQUEST_ENTER_PARTY)
				else:
					self.__ShowButton(localeInfo.TARGET_BUTTON_INVITE_PARTY)

			if player.IsRevengeInstance(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)
				self.__ShowButton(localeInfo.TARGET_BUTTON_AVENGE)
			elif player.IsChallengeInstance(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)
				self.__ShowButton(localeInfo.TARGET_BUTTON_ACCEPT_FIGHT)
			elif player.IsCantFightInstance(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)

			if not player.IsSameEmpire(self.vid):
				self.__HideButton(localeInfo.TARGET_BUTTON_INVITE_PARTY)
				self.__HideButton(localeInfo.TARGET_BUTTON_FRIEND)
				self.__HideButton(localeInfo.TARGET_BUTTON_FIGHT)

		distance = player.GetCharacterDistance(self.vid)
		if distance > self.EXCHANGE_LIMIT_RANGE:
			self.__HideButton(localeInfo.TARGET_BUTTON_EXCHANGE)
			self.__ArrangeButtonPosition()

		self.__ArrangeButtonPosition()

	def __ArrangeButtonPosition(self):
		showingButtonCount = len(self.showingButtonList)

		pos = -(showingButtonCount / 2) * 68
		if 0 == showingButtonCount % 2:
			pos += 34

		for button in self.showingButtonList:
			button.SetPosition(pos, 33)
			pos += 68

		self.SetSize(max(150, showingButtonCount * 75), 65)
		self.UpdatePosition()

	def OnUpdate(self):
		if player.IsPVPInstance(self.vid):
				if app.GetTime() > self.SaveSecond:
					self.SaveSecond = app.GetTime()+0.2
					if str(chr.GetNameByVID(self.vid))!="None":
						net.SendWhisperPacket(str(self.name.GetText()), "CODE_MESSAGE_OPPONENTS_HP_29305|"+str(player.GetMainCharacterIndex()))
					if constInfo.OPPONENTS_HP[1]!=0:
						if constInfo.OPPONENTS_HP[0]<=0:
							self.SetHP(0)
						else:
							self.SetHP(((float(constInfo.OPPONENTS_HP[0])/float(constInfo.OPPONENTS_HP[1]))*100))
	
						self.HPText.SetText("%d/%d" % (constInfo.OPPONENTS_HP[0], constInfo.OPPONENTS_HP[1]))
						self.HPText.Show()

		else:
			self.HPText.Hide()
							
		if self.isShowButton:

			exchangeButton = self.buttonDict[localeInfo.TARGET_BUTTON_EXCHANGE]
			distance = player.GetCharacterDistance(self.vid)

			if distance < 0:
				return

			if exchangeButton.IsShow():
				if distance > self.EXCHANGE_LIMIT_RANGE:
					self.RefreshButton()

			else:
				if distance < self.EXCHANGE_LIMIT_RANGE:
					self.RefreshButton()
