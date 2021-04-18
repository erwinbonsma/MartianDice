pico-8 cartridge // http://www.pico-8.com
version 32
__lua__
--consts,vars,utils
local_run=false
version="0.22"

phase={
 throwing=1,
 thrown=2,
 movedtanks=3,
 pickdice=4,
 pickeddice=5,
 checkpass=6,
 done=7
}

endcause={
 [1]="cannot improve score",
 [2]="player choice",
 [3]="no more dice",
 [4]="cannot select a die",
 [5]="defeated!",
 [6]="turn forcefully ended"
}

errormsg={
 [1]="room not found",
 [2]="invalid name",
 [3]="name already in use",
 [4]="player limit reached",
 [5]="internal server error"
}

menuitems={
 "change name",
 "enter public room",
 "create private room",
 "enter private room"
}

--label,xpos
buttons={
 {"start",0},
 {"help",29},
 {"send",82},
 {"exit",107}
}

chatmsg={
 "hi","bye","yes","no","okay",
 "thx","wow","oops","gg",
 "play?","wait?"
}

help={
 "abduct earthlings",
 "",
 "+1 point for each",
 "+3 points for all three types",
 "",
 "  you must beat",
 " earth's defence",
 "",
 "  die faces:",
 "",
 "after your dice are thrown:",
 "1. tanks are set aside",
 "2. you select a set of dice",
 "",
 "your turn ends when:",
 "- you cannot defeat the tanks",
 "- you cannot select a die",
 "- you choose to stop",
 "",
 "you win by scoring 25 points",
 "",
}
helpscroll=5
helpmax=(#help-7)*helpscroll


vector={
 {1,0},{0,1},{-1,0},{0,-1}
}

public_room="pico"

--client names
pal1={12,13,2,15,6,3}
--bot names
pal2={7,8,11,10}

title={
 --flying saucer movement
 delta={{0,0},{0,0}},
 room=nil
}

menu={
 ypos=1, --menu-item
 xpos=0, --pos in text entry
 room="****",
 name="p8-"..chr(
  ord("a")+flr(rnd(26))
 ),
 blink=0,
}

room={
 id=""
}

function shuffle(l)
 for i=1,#l do
  local j=flr(rnd(#l-i+1))+i
  if i!=j then
   local tmp=l[i]
   l[i]=l[j]
   l[j]=tmp
  end
 end
 return l
end

function print_outlined(
 msg,x,y,c1,c2,c3
)
 color(c3)
 print(msg,x+1,y+1)

 color(c2)
 print(msg,x-1,y)
 print(msg,x+1,y)
 print(msg,x,y-1)
 print(msg,x,y+1)

 color(c1)
 print(msg,x,y)
end

function print_select(
 msg,x,y,selected
)
 if not selected then
  print(msg,x,y,4)
 else
  print_outlined(msg,x,y,9,4,0)
 end
end

function modchar(
 s,idx,to,allowspace
)
 local from=sub(s,idx,idx)
 if from<"a" or from>"z" then
  from=nil
 end

 if to==⬆️ then
  if from==nil then
   to="a"
  elseif from=="z" then
   if allowspace then
    to=" "
   else
    to="a"
   end
  else
   to=chr(ord(s,idx)+1)
  end
 elseif to==⬇️ then
  if from==nil then
   to="z"
  elseif from=="a" then
   if allowspace then
    to=" "
   else
    to="z"
   end
  else
   to=chr(ord(s,idx)-1)
  end
 end

 local snew=""
 if idx>1 then
  snew=sub(s,1,idx-1)
 end
 if idx<#s or to!=" " then
  snew=snew..to
 end
 if idx<#s then
  snew=snew..sub(s,idx+1)
 end
 return snew
end

function is_roomid_set()
 for i=1,4 do
  local ch=sub(menu.room,i,i)
  if ch<"a" or ch>"z" then
   return false
  end
 end

 return true
end

function roundrect(x0,y0,x1,y1,c)
 line(x0+2,y0,x1-2,y0,c)
 line(x0+2,y1,x1-2,y1,c)
 line(x0,y0+2,x0,y1-2,c)
 line(x1,y0+2,x1,y1-2,c)
 pset(x0+1,y0+1,c)
 pset(x0+1,y1-1,c)
 pset(x1-1,y0+1,c)
 pset(x1-1,y1-1,c)
end

function actionbtnp()
 return btnp(❎) or btnp(🅾️)
end

-->8
--drawing
function draw_rrect(
 x,y,w,h
)
 rectfill(x+1,y+1,x+w-1,y+h-1)

 line(x,y+1,x,y+h-1,15)
 line(x+1,y,x+w-1,y,15)
 line(x+w,y+1,x+w,y+h-1,5)
 line(x+1,y+h,x+w-1,y+h,5)
end

function draw_button(
 label,x,y,w,selected,disabled
)
 color(4)
 if (selected) color(13)
 draw_rrect(x,y,w,8)

 color(15)
 if (disabled) color(5)
 print(label,x+3,y+2)
end

function draw_vscroll(
 x,y1,y2,progress
)
 line(x+3,y1,x+3,y2,5)
 local y=y1+(y2-y1-5)*progress
 color(4)
 draw_rrect(x,y,6,4)
 local c=15
 if (progress<0.01) c=5
 rectfill(x+2,y1-4,x+5,y1-2,c)
 c=15
 if (progress>0.99) c=5
 rectfill(x+2,y2+1,x+5,y2+3,c)
 print("⬆️",x,y1-5,4)
 print("⬇️",x,y2,4)
end

function add_chat(
 sender,msg,prefix
)
 if (prefix==nil) prefix=""
 local w=6+(#msg+#prefix)*4
 if #room.chatlog>0 then
  local l=room.chatlog[
   #room.chatlog
  ]
  local e=l[#l]
  local x=e[4]+w
  if x<128 then
   --msg fits on this line
   add(l,{prefix,sender,msg,x+4})
   return
  end
 end
 --need to start a new line
 add(room.chatlog,{
  {prefix,sender,msg,w+4}
 })
 if #room.chatlog>3 then
  --remove oldest line
  deli(room.chatlog,1)
 end
end

function draw_chatlog(y0)
 for i,l in pairs(room.chatlog) do
  local x=0
  local y=i*6+y0
  for chat in all(l) do
   local c=pal1[chat[2]]
   print(chat[1],x,y,c)
   x+=#chat[1]*4
   spr(chat[2]+31,x,y)
   print(chat[3],x+6,y,c)
   x=chat[4]
  end
 end
end

function draw_throw(throw)
 local selected=0
 if game.pickdie
 and animate==nil then
  selected=game.pickdie[
   game.die_idx
  ]
 end

 for d in all(throw) do
  spr(2+2*d.tp,d.x,d.y,2,2)
  if d.tp==selected then
   roundrect(
    d.x-1,d.y-1,d.x+15,d.y+15,15
   )
  end
 end
end

function draw_battle(battle)
 for d in all(battle) do
  spr(2+d.tp*2,d.x,d.y,2,2)
 end
end

function draw_collected(collected)
 for tp,l in pairs(collected) do
  for d in all(l) do
   spr(2+d.tp*2,d.x,d.y,2,2)
  end
 end
end

function title_draw(y0,c2)
 --logo
 pal(3,4)
 spr(128,32,y0,9,4)
 pal()

 --flying saucers
 palt(1,true)
 pal(11,9)
 for i=1,2 do
  local d=title.delta[i]
  local x=86*i-72+d[1]
  local y=y0+d[2]+2
  spr(4,x,y,2,2)
 end
 palt()
 pal()

 if (title.room==nil) return

 print(
  "room "..title.room,
  52,y0+35,c2
 )

 pal(7,c2)
 if title.public then
  spr(49,40,y0+33)
 else
  spr(48,40,y0+33)
 end
 pal()
end

function edit_draw(s,x,y)
 color(15) --default
 if menu.xpos>0 then
  if menu.xpos<=menu.editlen then
   color(9)
   if menu.blink<0.5 then
    s=modchar(s,menu.xpos,"_")
   end
  end
 end
 print(s,x,y)
end

function menu_draw()
 cls(0)
 color(3)
 print(version)

 title_draw(8,15)

 for i=1,4 do
  local txt=menuitems[i]
  local x=64-2*#txt
  local y=60+i*10
  print_select(
   txt,x,y,
   menu.ypos==i and menu.xpos==0
  )
 end

 print("name",52,52,15)
 if menu.ypos==1 then
  edit_draw(menu.name,72,52)
 else
  print(menu.name,72,52,15)
 end

 if menu.ypos==4 then
  edit_draw(menu.room,72,43)

  if menu.xpos>0
  and is_roomid_set() then
   draw_button(
    "go",90,41,14,menu.xpos==5
   )
  end
 end

 if menu.status_msg!=nil then
  print(
   menu.status_msg,
   64-2*#menu.status_msg,
   120,
   menu.status_color
  )
 end
end

function game_draw()
 cls(0)

 for i=0,2 do
  rectfill(
   6,7+37*i,121,41+37*i-i\2,4
  )
 end
 
 color(4)
 print("round "..game.round,0,0)
 print("throw "..game.thrownum,100,0)

 local ap=game.active_player
 local x=60-#ap.name*2
 spr(ap.avatar,x,0)
 print(ap.name,x+7,0,ap.color)

 palt(14,true)
 palt(0,false)
 draw_throw(game.throw)
 draw_battle(game.battle)
 draw_collected(game.collected)
 palt()

 if game.endcause!=0 then
  local msg=endcause[game.endcause]
  print_outlined(
   msg,64-2*#msg,15,11,1,0
  )
  
  msg="+"..game.scored.." => "
  msg=msg..game.score.."(#"
  msg=msg..game.position..")"
  print_outlined(
   msg,64-2*#msg,26,11,1,0
  )
 end

 if game.chkpass then
  rectfill(27,26,99,36,4)
  print("continue?",29,29,15)
  draw_button(
   "yes",67,27,16,not game.pass
  )
  draw_button(
   "no",86,27,12,game.pass
  )
 end

 draw_chatlog(111)
end

function draw_help()
 local ysub=flr(
  (room.help%helpscroll)*6
  /helpscroll
 )
 for i=1,7 do
  local y=6*i+44-ysub
  local j=i+room.help\helpscroll
  print(help[j],0,y,15)
  if j==1 then
   spr(8,72,y-2,6,2)
  elseif j==6 then
   spr(4,72,y-2,2,2)
   spr(6,100,y-2,2,2,true)
   spr(3,90,y-2,1,2)
  elseif j==9 then
   for i=1,6 do
    local x=40+i*10
    rectfill(x+1,y-2,x+7,y+6,1)
    rectfill(x,y-1,x+8,y+5,1)
    spr(37+i,x+1,y-1)
   end
  end
 end
 
 draw_vscroll(
  121,50,86,room.help/helpmax
 )
end

function draw_room_member_1col(
 n,sprite,name,c
)
 local y=50+n*8
 spr(sprite,51,y)
 print(name,58,y,c)
end

function draw_room_member_2cols(
 n,sprite,name,c
)
 local x=32+(n%2)*34
 local y=50+flr(n/2)*8
 spr(sprite,x,y)
 print(name,x+7,y,c)
end

function draw_room_members()
 local n=0
 local drawfun=draw_room_member_1col
 if room.size>4 then
  drawfun=draw_room_member_2cols
 end
 for id,name in pairs(room.clients) do
  drawfun(
   n,31+id,name,pal1[id]
  )
  n+=1
 end
 for bot in all(room.bots) do
  local tp=bot[2]
  drawfun(
   n,49+tp,bot[1],pal2[tp]
  )
  n+=1
 end
end

function room_draw()
 cls()

 title_draw(0,4)

 if room.help!=nil then
  draw_help()
 else
  draw_room_members()
 end
 
 local disabled={
  room.host==0,
  false,
  room.chatidx==0
  or peek(a_chat_msg_out)!=0,
  false
 }
 for i,b in pairs(buttons) do
  draw_button(
   b[1],b[2],98,#b[1]*4+4,
   room.ypos==i,disabled[i]
  )
 end
 rect(54,98,80,106,5)
 local msg=chatmsg[room.chatidx]
 if (msg==nil) msg="chat"
 color(4)
 if (room.ypos==3) color(9)
 print(msg,68-2*#msg,100)

 draw_chatlog(115)
end

-->8
-- animations
function animate_throw(throw)
 local update_tp=function(d)
  local old=d.tp
  d.tp=max(1,flr(
   d.target_tp-1+(
    d.entropy/20
   )^2
  )%6)
  if d.tp!=old then
   sfx(0)
  end
 end

 for d in all(throw) do
  d.target_tp=d.tp
  d.entropy=60+rnd(8)^2
  update_tp(d)
 end
 
 animate=function()
  local done=true
  for d in all(throw) do
   if d.entropy!=nil then   
    d.entropy-=1
    if d.entropy<0 then
     d.tp=d.target_tp
     d.target_tp=nil
     d.entropy=nil
     sfx(1)
    else
     update_tp(d)
    end
    done=false
   end
  end
  
  if done then
   animate=nil
  end
 end
end

-->8
--gpio

--general ctrl flags
--0:ready for write
--1:ready for read

--5:start game (set by p8)
--6:starting game
a_ctrl_in_game=0x5f80

--4:start batch/reset
a_ctrl_in_room=0x5f81

--2:null
--3:awaiting input (set by p8)
a_ctrl_out=0x5f82

a_errr=0x5f83
a_ctrl_dump=0x607f --tmp

a_move=0x5f84

--0:none
--1:initiate join (set by p8)
--2:initiating join
--3:joined
--4:initiate exit (set by p8)
--5:initiating exit
--6:initiate create (set by p8)
--7:initiating create
--8:error
a_room_mgmt=0x5f85
a_room=0x5f86 -- 4 bytes
a_name=0x5f8a -- 6 bytes

--- game status ---
a_thrw=0x5f90 -- 5 bytes
a_side=0x5f95 -- 5 bytes

--scoring
a_endc=0x5f9a --end cause
a_trsc=0x5f9b --turn score
a_ttsc=0x5f9c --tot. score
a_cpos=0x5f9d --cur. position

--round/turn/throw/phase counters
a_crou=0x5fa0
a_ctur=0x5fa1
a_cthr=0x5fa2
a_cpha=0x5fa3
--active player, see a_ptyp
a_atyp=0x5fa4
a_anam=0x5fa5 -- 6 bytes

--- room status ---
--num clients/bots
a_ncli=0x5fb0
a_nbot=0x5fb1
--0/1: 1=>player is host
a_host=0x5fb2
--1..6 :client, id=value
--7..10:bot,    tp=value-6
a_ptyp=0x5fb3
--name, 0-chars when len<6
a_pnam=0x5fb4 -- 6 bytes

a_chat_out_msg=0x5fc0
a_chat_in_msg=0x5fc1
a_chat_in_sender=0x5fc2

function die_choices(g)
 local choice={}
 
 --add dice from throw
 for d in all(g.throw) do
  choice[d.tp]=true
 end
 assert(not choice[2])

 --remove collected earthlings
 for tp,l in pairs(g.collected) do
  choice[tp]=false
 end

 --add in order of throw
 local l={}
 for d in all(g.throw) do
  if choice[d.tp] then
   add(l,d.tp)
   choice[d.tp]=false
  end
 end
 
 return l
end

--updates collected while
--preserving order.
--old is dict: [tp]={die}
--new is dict: [tp]=num
function update_collected(
 old,new
)
 local n=0
 for tp,l in pairs(old) do
  n+=#l
 end

 local d={}
 for tp,num in pairs(new) do
  if num>0 then
   d[tp]=old[tp] or {}
   num-=#d[tp]
   assert(num>=0)
   for i=1,num do
    add(d[tp],{
     tp=tp,
     x=(n%7)*16+8,
     y=(n\7)*16+83
    })
    n+=1    
   end
  end
 end

 return d
end

-- num=[#rays, #tanks]
function set_battle(num)
 local l={}
 
 for tp=1,2 do
  local x=8
  local y=30+tp*16
  for i=1,num[tp] do
   add(l,{tp=tp,x=x,y=y})
   if i<7 then
    x+=16
   elseif i==7 then
    --overflow: switch rows
    y+=16-(tp-1)*32
   else
    --move back in overflow row
    x-=16
   end
  end
 end

 return l
end

function new_throw(dice)
 local l={}
 for tp,num in pairs(dice) do
  for i=1,num do
   add(l,{tp=tp})
  end
 end

 shuffle(l)

 for i,d in pairs(l) do
  d.x=((i-1)%7)*16+8
  d.y=((i-1)\7)*16+9
 end

 return l
end

--old is list, new is dict
function update_throw(old,new)
 local l={}
 for tp in all(old) do
  if tp!=0 and new[tp]>0 then
   add(l,tp)
   new[tp]-=1
  else
   add(l,0)
  end
 end

 --just in case, add new dice
 local i=1
 for tp,num in pairs(new) do
  while num>0 do
   while l[i]!=0 and i<13 do
    i+=1
   end
   l[i]=tp
   num-=1
  end
 end

 return l
end

function gpio_puts(a0,len,s)
 for i=1,len do
  local v=0
  if i<=#s then
   v=ord(s,i)
   if v>=97 and v<=122 then
    --subtract 32 to output as
    --uppercase ascii
    v-=32
   end
  end
  poke(a0+i-1,v)
 end
end

function gpio_gets(a0,len)
 local s=""

 for i=1,len do
  local v=peek(a0+i-1)
  if v!=0 then
   if (v>=65 and v<=90) v+=32
   s=s..chr(v)
  end
 end

 return s
end

game_gpio_read_delay=0
function read_gpio_game()
 if peek(a_ctrl_in_game)!=1 then
  return
 end
 if game_gpio_read_delay>0 then
  game_gpio_read_delay-=1
  return
 end
 
 local g={}
 g.round=peek(a_crou)
 g.turn=peek(a_ctur)
 g.thrownum=peek(a_cthr)
 g.phase=peek(a_cpha)

 g.endcause=peek(a_endc)
 g.scored=peek(a_trsc)
 g.score=peek(a_ttsc)
 g.position=peek(a_cpos)

 local dice={}
 for i=1,5 do
  dice[i]=peek(a_thrw+i-1)
 end

 if game==nil
 or g.thrownum!=game.thrownum
 or g.turn!=game.turn then
  g.throw=new_throw(dice)
 else
  g.throw=update_throw(
   game.throw,dice
  )
 end
 if g.phase==phase.thrown then
  g.throw=animate_throw(g.throw)
 end

 g.battle=set_battle(
  {peek(a_side),peek(a_side+1)}
 )

 dice={}
 for i=3,5 do
  dice[i]=peek(a_side+i-1)
 end
 if game==nil then
  g.collected=new_collected(dice)
 else
  g.collected=update_collected(
   game.collected,dice
  )
 end

 if peek(a_ctrl_out)==0 then
  --move expected
  if g.phase==phase.pickdice then
   g.pickdie=die_choices(g)
   g.die_idx=1
  end
  if g.phase==phase.checkpass then
   g.chkpass=true
   g.pass=false
  end
  poke(a_ctrl_out,3)
 end

 local ap={}
 local v=peek(a_atyp)
 if v<=6 then
  --client avatar
  ap.avatar=31+v
  ap.color=pal1[v]
 else
  --bot avatar
  ap.avatar=43+v
  ap.color=pal2[v-6]
 end
 ap.name=gpio_gets(a_anam,6)
 g.active_player=ap

 game=g 
 game_gpio_read_delay=60
 poke(a_ctrl_in_game,0)
end

--show client joins/leaves in
--chat log
function log_client_changes(
 old,new
)
 for id,name in pairs(old) do
  if new[id]==nil then
   add_chat(id,name,"-")
  end
 end

 for id,name in pairs(new) do
  if old[id]==nil then
   add_chat(id,name,"+")
  end
 end
end

function read_gpio_room()
 if peek(a_ctrl_in_room)==4 then
  roomnew={
   pclients=peek(a_ncli),
   pbots=peek(a_nbot),
   host=peek(a_host),
   size=0,
   clients={},
   bots={}
  }
  poke(a_ctrl_in_room,0)
  return
 end
 if peek(a_ctrl_in_room)!=1 then
  return
 end

 local r=roomnew
 assert(r!=nil)

 local name=gpio_gets(a_pnam,6)
 local typ=peek(a_ptyp)
 if typ<=6 then
  r.clients[typ]=name
  r.pclients-=1
 else
  add(r.bots,{name,typ-6})
  r.pbots-=1
 end
 r.size+=1
 assert(r.pclients>=0)
 assert(r.pbots>=0)

 if r.pclients==0
 and r.pbots==0 then
  --finished batch update
  log_client_changes(
   room.clients,r.clients
  )

  room.clients=r.clients
  room.bots=r.bots
  room.size=r.size
  roomnew=nil
 end

 poke(a_ctrl_in_room,0)
end

function read_gpio_chat()
 if peek(a_chat_in_msg)==0 then
  return
 end

 add_chat(
  peek(a_chat_in_sender),
  chatmsg[peek(a_chat_in_msg)]
 )
 poke(a_chat_in_msg,0)
end

function read_gpio()
 read_gpio_game()
 read_gpio_room()
 read_gpio_chat()
end

-->8
--update

function game_pickdie()
 local n=#game.pickdie
 if n>1 then
  if btnp(⬅️) then
   game.die_idx=(
    game.die_idx+n-2
   )%n+1
  elseif btnp(➡️) then
   game.die_idx=(
    game.die_idx%n+1
   )
  end
 end

 if actionbtnp() then
  poke(
   a_move,
   game.pickdie[game.die_idx]
  )
  poke(a_ctrl_out,1)
  game.pickdie=nil
 end
end

function game_chkpass()
 if btnp(⬅️) or btnp(➡️) then
  game.pass=not game.pass
 end

 if actionbtnp() then
  poke(
   a_move,
   game.pass and 6
  )
  poke(a_ctrl_out,1)
  game.chkpass=false
 end
end

function game_update()
 read_gpio()

 if game.pickdie then
  game_pickdie()
 elseif game.chkpass then
  game_chkpass()
 end

 if peek(a_room_mgmt)==0 then
  --exited room
  show_menu()
  return
 end

 if btnp(❎) then
  if peek(a_room_mgmt)==3 then
   --initiate room exit
   poke(a_room_mgmt,4)
  end
 end

 if animate then
  animate()
 end

 --tmp:debug 
 if btnp(🅾️) then
  poke(a_ctrl_dump,1)
 end
end

function room_update()
 if peek(a_room_mgmt)==0 then
  --exited room
  show_menu()
  return
 end

 if peek(a_ctrl_in_game)==6 then
  poke(a_ctrl_in_game,0)
 end

 if game!=nil then
  _update=game_update
  _draw=game_draw
  return
 end

 if btnp(⬅️)
 and room.help==nil then
  room.ypos=(room.ypos+2)%4+1
 elseif btnp(➡️)
 and room.help==nil then
  room.ypos=room.ypos%4+1
 elseif btnp(⬆️) then
  if room.help!=nil then
   room.helpdelta-=helpscroll*5
  else
   room.chatidx=(
    room.chatidx+#chatmsg-2
   )%#chatmsg+1
   room.ypos=3
  end
 elseif btnp(⬇️) then
  if room.help!=nil then
   room.helpdelta+=helpscroll*5
  else
   room.chatidx=(
    room.chatidx%#chatmsg+1
   )
   room.ypos=3
  end
 end
 
 if room.help!=nil then
  if room.helpdelta<0 then
   room.help=max(0,room.help-1)
   room.helpdelta+=1
  elseif room.helpdelta>0 then
   room.help=min(
    room.help+1,helpmax
   )
   room.helpdelta-=1
  end
 end
 
 if actionbtnp() then
  if room.ypos==1
  and room.host!=0 then
   --initiate game start
   poke(a_ctrl_in_game,5)
  elseif room.ypos==2 then
   if room.help!=nil then
    room.help=nil
   else
    room.help=0
    room.helpdelta=0
   end
  elseif room.ypos==3
  and room.chatidx!=0
  and peek(a_chat_out_msg)==0 then
   poke(
    a_chat_out_msg,room.chatidx
   )
   room.chatidx=0
  elseif room.ypos==4
  and peek(a_room_mgmt)==3 then
   --initiate room exit
   poke(a_room_mgmt,4)
  end
 end

 read_gpio()
 title_update()

 --tmp:debug 
 if btnp(🅾️) then
  poke(a_ctrl_dump,1)
 end
end

function enter_room(room_id)
 room.id=room_id
 room.ypos=1
 room.chatidx=0
 room.chatlog={}
 room.help=nil
 title.room=room_id

 poke(a_chat_in_msg,0)
 poke(a_chat_out_msg,0)

 --clear game status
 game=nil
 game_gpio_read_delay=0
 poke(a_ctrl_in_game,0)

 _update=room_update
 _draw=room_draw
end

function clear_room_status()
 room.bots={}
 room.clients={}
 room.size=0
 poke(a_ctrl_in_room,0)
end

function join_room(room_id)
 clear_room_status()

 gpio_puts(a_room,4,room_id)
 gpio_puts(a_name,6,menu.name)

 menu.status_msg="joining room..."
 menu.status_color=5

 --initiate join
 poke(a_room_mgmt,1)
end

function create_room()
 clear_room_status()

 gpio_puts(a_name,6,menu.name)

 menu.status_msg="creating room..."
 menu.status_color=5

 --initiate room creation
 poke(a_room_mgmt,6)
end

function edittext(
 s,max_xpos,allowspace
)
 if btnp(➡️) then
  menu.xpos=menu.xpos%max_xpos+1
  menu.blink=0
 elseif btnp(⬅️) then
  menu.xpos=(
   menu.xpos+max_xpos-2
  )%max_xpos+1
  menu.blink=0
 elseif btnp(⬆️)
 and menu.xpos<=menu.editlen then
  s=modchar(
   s,menu.xpos,⬆️,allowspace
  )
  menu.blink=0.5
 elseif btnp(⬇️)
 and menu.xpos<=menu.editlen then
  s=modchar(
   s,menu.xpos,⬇️,allowspace
  )
  menu.blink=0.5
 else
  menu.blink+=(1/30)
  if menu.blink>1 then
   menu.blink=0
  end
 end

 return s
end

function menu_edittext()
 local max_xpos=menu.editlen

 if menu.ypos==1 then
  menu.name=edittext(
   menu.name,
   min(#menu.name+1,max_xpos),
   menu.xpos>1
  )
 elseif menu.ypos==4 then
  if is_roomid_set() then
   --can move to go button
   max_xpos+=1
  end
  menu.room=edittext(
   menu.room,max_xpos,false
  )
 else
  assert(false)
 end

 if actionbtnp() then
  if menu.ypos==4
  and menu.xpos==max_xpos then
   join_room(menu.room)
  end
  menu.xpos=0
 end
end

function menu_itemselect()
 local yposold=menu.ypos

 if btnp(⬇️) then
  menu.ypos=menu.ypos%4+1
 elseif btnp(⬆️) then
  menu.ypos=(menu.ypos+2)%4+1
 elseif actionbtnp() then
  if menu.ypos==1 then
   menu.editlen=6
   menu.xpos=1
  elseif menu.ypos==2 then
   join_room(public_room)
  elseif menu.ypos==3 then
   create_room()
  elseif menu.ypos==4 then
   menu.editlen=4
   if is_roomid_set() then
    --can directly enter
    menu.xpos=5
   else
    --need to specify id first
    menu.xpos=1
   end
  end
 end

 if menu.ypos!=yposold then
  if menu.ypos==1 then
   title.room=nil
  elseif menu.ypos==2 then
   title.room=public_room
  elseif menu.ypos==3 then
   title.room="????"
  else
   title.room=""
  end
  title.public=(menu.ypos==2)
  menu.status_msg=nil
 end
end

function title_update()
 for i=1,2 do
  if rnd(10)<1 then
   local d=title.delta[i]
   local v=vector[flr(rnd(4))+1]
   for j=1,2 do
    d[j]=max(min(d[j]+v[j],1),-1)
   end
  end
 end
end

function menu_update()
 if peek(a_room_mgmt)==3 then
  enter_room(gpio_gets(a_room,4))

  --in case room was created
  if room.id!=public_room then
   menu.room=room.id
   menu.ypos=4
  end
 end
 if peek(a_room_mgmt)==8 then
  --failed to enter room
  local msg=errormsg[
   peek(a_errr)
  ]
  if msg!=nil then
   menu.status_msg="error: "..msg
  else
   menu.status_msg="error: "..peek(a_errr)
  end
  menu.status_color=8
  poke(a_room_mgmt,0)
 end

 if menu.xpos!=0 then
  menu_edittext()
 else
  menu_itemselect()
 end
 title_update()
end

function show_menu()
 _draw=menu_draw
 _update=menu_update

 menu.status_msg=nil
end
-->8
function dev_init_game()
 game={
  throw=new_throw(
   {[3]=3,[4]=2,[5]=1,[1]=4}
  ),
  battle=set_battle({9,3}),
  collected=update_collected(
   {},{[4]=2}
  ),
  round=1,
  turn=2,
  phase=phase.pickdice,
  thrownum=2,
  endcause=0,
  active_player={
   name="me",
   avatar=32,
   color=pal1[1]
  }
 }
 game.pickdie=die_choices(game)
 game.die_idx=1
 --game.chkpass=true
 --game.pass=false
 animate_throw(game.throw)

 room={
  chatlog={
   {{"",1,"hi",30}},
   {{"",2,"bye",30}},
  }
 }

 _update=game_update
 _draw=game_draw
 poke(a_ctrl_out,0)
 poke(a_room_mgmt,3)
end

function dev_init_room()
 room={
  clients={
   [1]="bob",
   [2]="eriban",
   [3]="alice",
   [5]="george",
   [4]="simon",
   [6]="rich"
  },
  bots={
   ["bot-1"]=3,
   ["bot-2"]=4
  },
  size=8,
  ypos=1,
  help=nil,
  chatidx=0,
  chatlog={}
 }
 title.room="pico"
 title.public=true

 _update=room_update
 _draw=room_draw
 poke(a_room_mgmt,3)
end

function _init()
 poke(a_room_mgmt,0)
 dev_init_game()

 --show_menu()
end

__gfx__
00000000bbbbbbb00000000009000000e0000000000000eee0000000000000eee0000000000000eee0000000000000eee0000000000000ee0000000000000000
00000000b00000b00000008009900000000000000000000e000000000000000e0000000aa000000e000000000000000e000000000000000e0000000000000000
00700700b0bbb0b08888888800990000000000000000000e000000000000000e000000a00a00000e007770777077700e00000ccccc00000e0000000000000000
00077000b0bbb0b00880008000099000000000000000000e000000000000000e000aa0aaaa0aa00e007007000700700e0000c00000c0000e0000000000000000
00077000b0bbb0b00880000000009900000000bbb000000e000000888008800e00a00a0000a00a0e000770000077000e000c0000000c000e0000000000000000
007007000b0b0b00880000000000099000000b000b00000e000008000880000e00a0a000000a0a0e000070707070000e00c00c000c00c00e0000000000000000
000000000bb0bb00880000000000990000000b000b00000e000008888800000e000a00000000a00e000070707070000e00c00c000c00c00e0000000000000000
0000000000bbb000000000000009900000bbbbbbbbbbb00e008888888888800e000a0a000000a00e000070000070000e00c000000000c00e0000000000000000
00cccc0007777770aa00a0aa009900900b00000000000b0e080000000000080e00aa00000000a00e000077777770000e00c0c00000c0c00e0000000000000000
0cccccc077777777aaaa00aa099009900b00000000000b0e080800000008080e0aaa00000000a00e000700000007000e00c00c000c00c00e0000000000000000
cc0cc0cc7707707700000a00090099000b00000000000b0e080000000000080e0000a000000a000e007000707000700e000c00ccc00c000e0000000000000000
cc0cc0cc7777777700a0a00a0009900000bbbbbbbbbbb00e008888888888800e00000a0000a0000e007000000000700e0000c00000c0000e0000000000000000
cccccccc7777777700a0a0a000990000000000000000000e000000000000000e000000aaaa00000e000700000007000e00000ccccc00000e0000000000000000
cc0cc0cc7707707700a0a0a009900000000000000000000e000000000000000e000000000000000e000077777770000e000000000000000e0000000000000000
0cc00cc077777777aa00a0aa09000000e0000000000000eee0000000000000eee0000000000000eee0000000000000eee0000000000000ee0000000000000000
00cccc0007777770aa00a0aa00000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee0000000000000000
0ccc0000ddddd00002220000ff0ff00006660000330330001111111011111110111111101a1a1a101711171011ccc11000000000000000000000000000000000
c0c0c00000d000002020200000f00000006000003303300011bbb11011bbb1108888811011aaa110177777101ccccc1000000000000000000000000000000000
ccccc000ddddd0002222200000f00000606060000030000011bbb11011bbb110118881101a1aaa1017171710cc1c1cc000000000000000000000000000000000
c000c000d000d00022022000f000f0006000600030003000bbbbbbb0bbbbbbb0888888801aaaaa1017171710ccccccc000000000000000000000000000000000
0ccc00000ddd0000222220000fff00000666000003330000bbbbbbb0bbbbbbb088888880aaaaaa1077777770c1ccc1c000000000000000000000000000000000
0000000000000000000000000000000000000000000000001bbbbb101bbbbb101888881011aaa110771717701c111c1000000000000000000000000000000000
000000000000000000000000000000000000000000000000111111101111111011111110111111101777771011ccc11000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
77777770007777007777700088888000bbbbb000aaaa000000000000000000000000000000000000000000000000000000000000000000000000000000000000
70000070077777707070700088888000bbbbb000000aa00000000000000000000000000000000000000000000000000000000000000000000000000000000000
70777070770770777777700008800000bbbbb000aa0aa00000000000000000000000000000000000000000000000000000000000000000000000000000000000
707770707707707770707000880000000bbb0000aa00000000000000000000000000000000000000000000000000000000000000000000000000000000000000
7077707077777777777770008800000000b000000aaaa00000000000000000000000000000000000000000000000000000000000000000000000000000000000
07070700770770770000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
07707700077007700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00777000007777000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00bbbbbbbbbbbbb00000000000000000007777777777700000000cccccc000000000000aa0000000000000000000000000000000000000000000000000000000
00bbbbbbbbbbbbb000000000000080800777777777777700000cccccccccc0000aaaa00aa00aaaa0000000000000000000000000000000000000000000000000
00bb000000000bb00888888888888888770007777700077000cccccccccccc000aaaaaaaa00aaaa0000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb0088888888888888877000777770007700cccccccccccccc00aaaaaaa000aaaa0000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb0088888888888888877000777770007700ccc00cccc00ccc00aaaa00000aaaaa0000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb000888800800080807777777777777770cccc00cccc00cccc000000000aaa0000000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb000888800800000007777770007777770cccccccccccccccc00000000aaa00000000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb000888800800000007777770007777770ccccccccccccccccaaa0000aaa000aaa000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb008888888000000007777770007777770ccccccccccccccccaaaa000aa000aaaa000000000000000000000000000000000000000000000000
000bb0bb0bb0bb0008888000000000007777777777777770cc0cccccccccc0cc00aa000aa000aa00000000000000000000000000000000000000000000000000
000bb0bb0bb0bb0008888000000000007700077777000770cc00cccccccc00cc00aa000aa000aa00000000000000000000000000000000000000000000000000
000bbb0b0b0bbb00888800000000000077000777770007700cc00cccccc00cc00aaaa00aa00aaaa0000000000000000000000000000000000000000000000000
0000bbb000bbb000888800000000000077000777770007700ccc00000000ccc00aaaa00aa00aaaa0000000000000000000000000000000000000000000000000
00000bbb0bbb00008888000000000000077777777777770000ccc000000ccc000aaaa00aa00aaaa0000000000000000000000000000000000000000000000000
000000bbbbb0000000000000000000000077777777777000000cccccccccc0000aaaa00aa00aaaa0000000000000000000000000000000000000000000000000
0000000bbb0000000000000000000000000000000000000000000cccccc000000000000aa0000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00030000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00033000003300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00033300033300000000000000000000000000000033000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00333333333330000000300000000000000000000033000000300000030000030000000000000000000000000000000000000000000000000000000000000000
00330333330330000000300000000000000000000000000000300000030000030000000000000000000000000000000000000000000000000000000000000000
00330333330330000003330033333330033333333333300003330000033000330000000000000000000000000000000000000000000000000000000000000000
00330033300330000003330000333333000333333000000003330000033000330000000000000000000000000000000000000000000000000000000000000000
03330033300333000003030000033003300003300033000003030000033300330000000000000000000000000000000000000000000000000000000000000000
03330003000333000033033000033003300003300033000033033000033300330000000000000000000000000000000000000000000000000000000000000000
03330003000333000030003000033003300003300033000030003000033330330000000000000000000000000000000000000000000000000000000000000000
03330003000333000330003300033333000003300033000330003300033030330000000000000000000000000000000000000000000000000000000000000000
03330003000333000333333300033333000003300033000333333300033033330000000000000000000000000000000000000000000000000000000000000000
03330000000333000330003300033003000003300033000330003300033003330000000000000000000000000000000000000000000000000000000000000000
03330000000333000330003300033003300003300033000330003300033003330000000000000000000000000000000000000000000000000000000000000000
03330000000333000330003300033003300033330333300330003300033000330000000000000000000000000000000000000000000000000000000000000000
33333000003333303330003330333003330033330333303330003330333000333000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000003333330033330033333300333333000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000033333003300333330003333300000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000033000033303303330000033300000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000003300003303303300000033000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000003300003303303300000033330000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000003300003303303300000033333300000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000003300003303303300000033330000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000003300003303303300000033000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000033000033303303330000033300000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000033333003300333330003333300000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000003333330033330033333300333333000000000000000000000000000000000000000000000000000000000000000000000000000000000
__label__
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000300000003000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000330000033000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000333000333000000000000000000000000000000330000000000000000000000000000000000000000000000000000
00000000000000000000000000000000003333333333300000003000000000000000000000330000003000000300000300000000000000000000000000000000
00000000000000000000000000000000003303333303300000003000000000000000000000000000003000000300000300000000000000000000000000000000
00000000000000000000000000000000003303333303300000033300333333300333333333333000033300000330003300000000000000000000000000000000
00000000000000000000000000000000003300333003300000033300003333330003333330000000033300000330003300000000000000000000000000000000
00000000000000000000000000000000003300333003330000030300000330033000033000330000030300000333003300000000000000000000000000000000
00000000000000000000000000000000033300030003330000330330000330033000033000330000330330000333003300000000000000000000000000000000
00000000000000000000000000000000033300030003330000300030000330033000033000330000300030000333303300000000000000000000000000000000
00000000000000000000000000000000033300030003330003300033000333330000033000330003300033000330303300000000000000000000000000000000
00000000000000000000000000000000033300030003330003333333000333330000033000330003333333000330333300000000000000000000000000000000
00000000000000000000000000000000033300000003330003300033000330030000033000330003300033000330033300000000000000000000000000000000
00000000000000000000000000000000033300000003330003300033000330033000033000330003300033000330033300000000000000000000000000000000
00000000000000000000000000000000033300000003330003300033000330033000333303333003300033000330003300000000000000000000000000000000
00000000000000000000000000000000333330000033333033300033303330033300333303333033300033303330003330000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000033333300333300333333003333330000000000000000000000000000000000000000000000000
000000000000000000000000000000000000000bbb00000000000333330033003333300033333000000000bbb000000000000000000000000000000000000000
00000000000000000000000000000000000000b000b000000033000033303303330000033300000000000b000b00000000000000000000000000000000000000
00000000000000000000000000000000000000b000b000000003300003303303300000033000000000000b000b00000000000000000000000000000000000000
00000000000000000000000000000000000bbbbbbbbbbb000003300003303303300000033330000000bbbbbbbbbbb00000000000000000000000000000000000
0000000000000000000000000000000000b00000000000b0000330000330330330000003333330000b00000000000b0000000000000000000000000000000000
0000000000000000000000000000000000b00000000000b0000330000330330330000003333000000b00000000000b0000000000000000000000000000000000
0000000000000000000000000000000000b00000000000b0000330000330330330000003300000000b00000000000b0000000000000000000000000000000000
00000000000000000000000000000000000bbbbbbbbbbb000033000033303303330000033300000000bbbbbbbbbbb00000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000333330033003333300033333000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000033333300333300333333003333330000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

__map__
00000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
__sfx__
000100001d05000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
000200001a05000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
