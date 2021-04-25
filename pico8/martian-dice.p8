pico-8 cartridge // http://www.pico-8.com
version 32
__lua__
-- martian dice
-- (c) 2021, erwin bonsma

phase={
 throwing=1,
 thrown=2,
 movedtanks=3,
 pickdice=4,
 pickeddice=5,
 checkpass=6,
 done=7,
 endgame=8
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
 msg,x,y,c1,c2
)
 color(c2)
 print(msg,x-1,y)
 print(msg,x+1,y)
 print(msg,x,y-1)
 print(msg,x,y+1)

 color(c1)
 print(msg,x,y)
end

function print_select(
 msg,x,y,selected,active
)
 if selected and active then
  print_outlined(msg,x,y,9,0,0)
 else
  print(
   msg,x,y,
   selected and 7 or 15
  )
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

function clone_log(log)
 local out={}
 local n=#log

 if (n==0) return out

 --shallow copy all lines
 foreach(
  log,
  function(l) add(out,l) end
 )

 --deep-copy last line
 out[n]={}
 foreach(
  log[n],
  function(l) add(out[n],l) end
 )

 return out
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
 color(selected and 9 or 4)
 draw_rrect(x,y,w,8)

 color(selected and 7 or 15)
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

function draw_animation()
 if animate and animate.draw then
  animate.draw()
 end
end

function add_chat(
 log,sender,msg,prefix,wip
)
 if (prefix==nil) prefix=""
 local w=6+(#msg+#prefix)*4
 local entry={
  prefix=prefix,
  sender=sender,
  msg=msg,
  clr=pal1[sender]
 }
 if (wip) entry.clr=9
 
 if #log>0 then
  local l=log[#log]
  local e=l[#l]
  local x=e.xnext+w
  if x<128 then
   --msg fits on this line
   entry.xnext=x+4
   add(l,entry)
   return
  end
 end

 --need to start a new line
 entry.xnext=w+4
 add(log,{entry})

 if #log>3 then
  --remove oldest line
  deli(log,1)
 end
end

function _draw_chatlog(log,y0,n)
 local i0=1+max(#log-n,0)
 for i,l in pairs(log) do
  if i>=i0 then
   local x=0
   local y=(i-i0)*6+y0
   for e in all(l) do
    print(e.prefix,x,y,e.clr)
    x+=#e.prefix*4
    pal(pal1[e.sender],e.clr)
    spr(e.sender+31,x,y)
    pal()
    print(e.msg,x+6,y,e.clr)
    x=e.xnext
   end
  end
 end
end

function draw_chatlog(y0,n)
 local log=room.chatlog

 if room.chatidx!=0
 and room.chat_active then
  --add wip message
  log=clone_log(room.chatlog)
  add_chat(
   log,1,
   chatmsg[room.chatidx],
   nil,true
  )
 end

 _draw_chatlog(log,y0,n)
end

function draw_popup_msg(msg,y)
 rectfill(0,y,127,y+7,5)
 print(msg,2,y+1,9)
end

function draw_thrown_die(
 d,scale
)
 local sz=15*scale
 local h1=sz
 local w1=sz
 local h2=sz
 local w2=sz

 local tp1=d.tp
 local tp2=d.tp_prv

 local frac=
  max(0,min(1,1-d.shift*2))
 
 if flr(d.rolldir)>=2 then
  local tmp=tp1
  tp1=tp2
  tp2=tmp
  frac=1-frac
 end
 if flr(d.rolldir)%2==0 then
  w1*=frac
  w2=sz-w1
 else
  h1*=frac
  h2=sz-h1
 end
  
 sspr(
  16+tp1*16,0,15,15,
  d.x,d.y,w1,h1
 )
 sspr(
  16+tp2*16,0,15,15,
  d.x+sz-w2,d.y+sz-h2,w2,h2
 )
end

function draw_dice(dice)
 for d in all(dice) do
  spr(2+d.tp*2,d.x,d.y,2,2)
  if d.entropy!=nil then
   draw_thrown_die(d,1)
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

 draw_dice(throw)
 for d in all(throw) do
  if d.tp==selected then
   roundrect(
    d.x-1,d.y-1,d.x+15,d.y+15,15
   )
  end
 end
end

function title_draw(c2)
 rectfill(26,0,101,35,4)

 palt(14,true)

 --logo
 palt(0,false)
 pal(4,9)
 spr(128,28,2,9,4)
 pal(4,4)

 palt(0,true)

 --earthlings
 for e in all(title.earthlings) do
  local x=e.x
  local show=true
  if e.y<112 then
   local i=(x<64 and 1) or 2
   x+=title.delta[i][1]
   
   show=(
    e.y>(1+title.delta[1][2])
   )
  end

  if show then
   spr(e.tp*2+2,x,e.y,2,2,e.flip)
  end
 end

 --flying saucers
 pal(11,9)
 for i=1,2 do
  local d=title.delta[i]
  local x=97*i-89+d[1]
  local y=d[2]+2
  rectfill(x,y,x+14,y+11,0)
  spr(4,x,y,2,2)
 end
 pal()

 if (title.room==nil) return

 print(
  "room "..title.room,47,40,c2
 )

 pal(7,c2)
 if title.public then
  spr(49,38,38)
 else
  spr(48,38,38)
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

 title_draw(15)

 for i=1,4 do
  local txt=menuitems[i]
  local x=64-2*#txt
  local y=54+i*10
  
  rectfill(24,y-2,103,y+6,4)

  print_select(
   txt,x,y,
   menu.ypos==i,
   menu.xpos==0
  )
 end

 print("name",47,48,15)
 if menu.ypos==1 then
  edit_draw(menu.name,67,48)
 else
  print(menu.name,67,48,15)
 end

 if menu.ypos==4 then
  edit_draw(menu.room,67,40)

  if menu.xpos>0
  and is_roomid_set() then
   draw_button(
    "go",87,38,12,menu.xpos==5
   )
  end
 end

 draw_animation()
end

function qr_draw()
 cls(0)
 
 title_draw(15)

 rectfill(31,42,96,107,7)
 palt(0,false)
 palt(14,true)
 sspr(0,96,32,32,33,44,64,64)
 palt()
end

function draw_winner(
 r,xc,yc,earthlings
)
 local winner=game.winner

 sspr(
  (winner.avatar%16)*8,
  (winner.avatar\16)*8,
  8,8,
  xc-flr(2.5*r),
  yc-flr(2.5*r),
  8*r,8*r
 )
 
 local msg=winner.name.." wins!"
 print(
  msg,xc-2*#msg+1,yc+15,
  winner.color
 )
 palt(14,true)
 pal(11,winner.color)
 spr(4,xc-31,yc-8,2,2)
 spr(4,xc+16,yc-8,2,2)

 for e in all(earthlings) do
  spr(
   4+2*e.tp,e.x,100,2,2,e.dx>0
  )
 end

 pal()
end

function game_draw()
 cls()

 color(4)
 print("round "..game.round,0,0)
 print("throw "..game.thrownum,100,0)

 local ap=game.active_player
 local x=60-#ap.name*2
 spr(ap.avatar,x,0)
 print(ap.name,x+7,0,ap.color)

 draw_chatlog(117,2)
 draw_animation()

 if (game.winner!=nil) return

 for i=0,2 do
  rectfill(
   6,7+37*i,121,41+37*i-i\2,4
  )
 end
 
 palt(14,true)
 palt(0,false)
 draw_throw(game.throw)
 draw_dice(game.battle)
 draw_dice(game.collected)
 palt()

 if game.endcause!=0 then
  local msg=endcause[game.endcause]
  print_outlined(
   msg,64-2*#msg,26,9,0
  )
  
  msg="+"..game.scored.."   "
  local l1=#msg
  msg=msg..game.score.."(#"
  msg=msg..game.position..")"
  local x=64-2*#msg
  print_outlined(msg,x,34,9,0)
  pal(4,0)
  spr(54,x+l1*4-11,33,2,1)
  pal()
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
end

function draw_help_line(i,x,y)
 palt(14,true)
 print(help[i],x,y,15)
 if i==1 then
  spr(8,x+72,y-2,6,2)
 elseif i==6 then
  spr(4,x+72,y-2,2,2)
  spr(6,x+100,y-2,2,2,true)
  spr(3,x+90,y-2,1,2)
 elseif i==9 then
  x+=40
  for j=1,6 do
   x+=10
   rectfill(x+1,y-2,x+7,y+6,1)
   rectfill(x,y-1,x+8,y+5,1)
   spr(37+j,x+1,y-1)
  end
 end
end

function draw_all_help()
 cls(4)
 palt(0,false)
 pal(1,0)
 for i=1,#help do
  draw_help_line(i,5,i*6-2)
 end
end

function draw_help()
 local ysub=flr(
  (room.help%helpscroll)*6
  /helpscroll
 )
 for i=1,7 do
  draw_help_line(
   i+room.help\helpscroll,
   0,6*i+46-ysub
  )
 end
 
 draw_vscroll(
  121,52,89,room.help/helpmax
 )
end

function draw_room_member_1col(
 n,sprite,name,c
)
 local y=56+n*8
 spr(sprite,51,y)
 print(name,58,y,c)
end

function draw_room_member_2cols(
 n,sprite,name,c
)
 local x=32+(n%2)*34
 local y=56+(n\2)*8
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

 title_draw(4)

 if room.help!=nil then
  draw_help()
 else
  draw_room_members()
 end
 
 local disabled={
  room.host!=1,
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

 draw_chatlog(110,3)
 draw_animation()
end

function draw_intro_dice(dice)
 palt(14,true)

 for d in all(dice) do
  local x=d.x
  local y=d.y

  rectfill(x,y,x+44,y+44,0)
  spr(56,x,y)
  spr(56,x+37,y,1,1,true)
  spr(56,x,y+37,1,1,false,true)
  spr(56,x+37,y+37,1,1,true,true)

  draw_thrown_die(d,3)
 end
end

function intro_draw()
 cls(4)

 --logo
 pal(4,9)
 palt(0,false)
 palt(14,true)
 spr(128,29,50,9,4)
 pal()

 palt()

 draw_animation()
end
-->8
-- animations
die_rolls={1,2,3,1,4,5}

function animate_throw(
 dice,wait_ticks
)
 local update_tp=function(d)
  local old=d.tp
  local f=(d.entropy/20)^2
  d.tp=die_rolls[1+(
   d.target_tp+5+
   --shift past second ufo in
   --die_rolls
   d.target_tp\4+
   flr(f)
  )%6]
  d.shift=f-flr(f)

  if d.tp!=old then
   d.tp_prv=old
   if (stat(16)<0) sfx(0)
   return true
  end
 end

 for d in all(dice) do
  d.target_tp=d.tp
  d.tp_prv=6
  d.rolldir=rnd(4)
  update_tp(d) 
 end
 
 animate={
  update=function()
   local done=true
   for d in all(dice) do
    if d.entropy!=nil then
     d.entropy-=0.4
     if d.entropy<4 then
      d.tp=d.target_tp
      d.target_tp=nil
      d.shift=0
      d.entropy=nil
      sfx(1)
     elseif update_tp(d) then
      d.rolldir=(
       d.rolldir+rnd(1)+3.5
      )%4
     end
     done=false
    end
   end
  
   if (done) wait(wait_ticks)
  end
 }
end

function animate_game_throw(
 dice
)
 local i=0
 for d in all(dice) do
  d.entropy=30+i*4*(1+rnd(1))
  i+=1
 end

 animate_throw(dice,30)
end

function animate_intro()
 local dice={}

 for i=0,3 do
  add(dice,{
   x=3+(i%2)*77,
   y=3+(i\2)*77,
   tp=i+2*(1-i%2),
   entropy=60+i*8
  })
 end

 animate_throw(dice,90)
 animate.draw=function()
  draw_intro_dice(dice)
 end
end

function animate_move(
 old,new,src
)
 assert(
  #old<#new,
  "#old="..#old..",#new="..#new
 )
 local moving={}
 
 for i=#new,#old+1,-1 do
  local j=#src
  local d=new[i]
  while j>0 
  and src[j].tp!=d.tp do
   j-=1
  end
  if j>0 then
   --found the new die in src
   --so animate it
   d.dstx=d.x
   d.dsty=d.y
   d.srcx=src[j].x
   d.srcy=src[j].y
   d.x=d.srcx
   d.y=d.srcy
   d.t=0

   add(moving,d)   
   deli(src,j)
  end
 end
 
 local tmax=30
 if (#moving==0) return
 
 animate={
  update=function()
   local done=true
   for d in all(moving) do
    d.t+=1
    if d.t==tmax then
     d.x=d.dstx
     d.y=d.dsty
     d.dstx=nil
     d.dsty=nil
     d.srcx=nil
     d.srcy=nil
    else
     d.x=d.srcx+(
      d.dstx-d.srcx
     )*d.t/tmax
     d.y=d.srcy+(
      d.dsty-d.srcy
     )*d.t/tmax

     done=false
    end
   end
   
   if (done) animate=nil
  end
 }
end

function wait(frames)
 if (animate==nil) animate={}
 animate.update=function()
  frames-=1
  if (frames<0) animate=nil
 end
end

function set_game_animation(
 g,moving
)
 local p=g.phase
 if p==phase.thrown then
  animate_game_throw(g.throw)
 elseif p==phase.movedtanks then
  animate_move(
   game.battle,g.battle,moving
  )
 elseif p==phase.pickeddice then
  if #game.battle<#g.battle then
   animate_move(
    game.battle,g.battle,moving
   )
  else
   animate_move(
    game.collected,g.collected,
    moving
   )
  end
 elseif p==phase.done then
  wait(60)
 else
  wait(10)
 end
end

function animate_endgame()
 if (animate!=nil) return

 local path={}
 local ap={}
 
 local earthlings={}
 local ticks=300
 
 --fairly complex function to
 --reduce jitter effects in the
 --animation. more specifically,
 --it avoids that the path
 --contains "empty triangles":
 -- e.g. *     *
 --      ** =>  *
 --it does so without causing
 --path incontinuities
 local getpoint=function(x,y)
  if ap.x==nil then
   ap.x=x
   ap.y=y
   return ap
  end
  
  local lp=ap
  if (#path>0) lp=path[#path]
    
  if lp.x==x and lp.y==y then
   return ap
  end

  add(path,{x=x,y=y})
  
  if (ap.x==x and ap.y==y)
  or abs(ap.x-x)>=2
  or abs(ap.y-y)>=2
  or (
   abs(lp.x-x)==1 
   and abs(lp.y-y)==1
  ) then
   ap.x=path[1].x
   ap.y=path[1].y
   deli(path,1)
   return ap
  end

  if #path==2 then
   ap.x=path[2].x
   ap.y=path[2].y
   path={}
   return ap
  end
  
  return ap
 end

 for i=1,12 do
  add(earthlings,{
   tp=i%3+2,
   x=56,
   dx=(i%2)*2-1,
   speed=0.2+rnd(2)
  })
 end

 local avatar_r=0
 local avatar_x=0
 local avatar_y=0

 animate={
  update=function()
 	 ticks-=1
	  if (ticks<=0) enter_room()

   local xc=64+flr(
    0.5+32*sin(time()*0.1)
   )
   local yc=50+flr(
    0.5+31*cos(time()*0.11)
   )
   local p=getpoint(xc,yc)
   avatar_x=p.x
   avatar_y=p.y

   avatar_r=4+flr(
    0.5+sin(time())
   )
  
   for e in all(earthlings) do
    e.x+=e.dx*e.speed
    if e.x<2 or e.x>109 then
     e.dx=-e.dx
    end
   end
  end,
  draw=function()
   draw_winner(
    avatar_r,avatar_x,avatar_y,
    earthlings
   )
  end
 }
end

function show_popup_msg(msg)
 local y=127

 local cr=cocreate(
  function()
   for i=1,6 do
    y-=1
    yield()
   end
  
   for i=1,60 do
    yield()
   end

   for i=1,7 do
    y+=1
    yield()
   end   
  end
 )
 
 animate={
  update=function()
   assert(coresume(cr))
   if (y>127) animate=nil
  end,
  draw=function()
   draw_popup_msg(msg,y)
  end
 }
end


-->8
--gpio

--general ctrl flags
--0:ready for write
--1:ready for read

--5:start game (set by p8)
--6:starting game
--7:bootstrapping (set by p8)
--8:bootstrapped
a_ctrl_in_game=0x5f80
a_handshke=0x5f80

--4:start batch/reset
a_ctrl_in_room=0x5f81

--2:null
--3:awaiting input (set by p8)
a_ctrl_out=0x5f82

a_errr=0x5f83

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
 for d in all(g.collected) do
  choice[d.tp]=false
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
--old is list: {die*}
--new is dict: [tp]=num
function update_collected(
 old,new
)
 local l={}

 --copy over existing
 for d in all(old) do
  if new[d.tp]>0 then
   add(l,d)
   new[d.tp]-=1
  end
 end

 --add new
 local n=#l
 for tp,num in pairs(new) do
  for i=1,num do
   add(l,{
    tp=tp,
    x=(n%7)*16+8,
    y=(n\7)*16+83
   })
   n+=1    
  end
 end

 return l
end

--old is list: {die*}
--new is dict: [tp]=num
function update_battle(old,new)
 local l={}
 local w={0,0}
 
 --copy over existing
 for d in all(old) do
  add(l,d)
  w[d.tp]+=1
 end

 for tp=1,2 do
  local x=8
  local y=30+tp*16
  assert(new[tp]>=w[tp])
  for i=1,new[tp] do
   if i>w[tp] then
    add(l,{tp=tp,x=x,y=y})
   end
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

--old is list, new is dict.
--all removed dice will be added
--to removed list, which should
--be empty
function update_throw(
 old,new,removed
)
 assert(#removed==0)
 local l={}
 for d in all(old) do
  if d!=nil and new[d.tp]>0 then
   add(l,d)
   new[d.tp]-=1
  else
   add(l,nil)
   add(removed,d)
  end
 end

 --sanity check
 for tp,num in pairs(new) do
  assert(
   num==0,
   "#["..tp.."]="..num
  )
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

function read_gpio_game()
 if peek(a_ctrl_in_game)!=1 then
  return
 end
 if animate!=nil then
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

 if g.phase==phase.endgame then
  g.winner=ap
  game=g
  return
 end
 
 local dice={}
 for i=1,5 do
  dice[i]=peek(a_thrw+i-1)
 end

 local sameturn=(
  game!=nil
  and game.turn==g.turn
 )
 local moving={}
 if sameturn
 and g.thrownum==game.thrownum then
  g.throw=update_throw(
   game.throw,dice,moving
  )
 else
  g.throw=new_throw(dice)
 end

 local prvb={}
 local prvc={}

 if sameturn then
  prvb=game.battle
  prvc=game.collected
 end

 dice={
  peek(a_side),peek(a_side+1)
 }
 g.battle=update_battle(
  prvb,dice
 )

 dice={}
 for i=3,5 do
  dice[i]=peek(a_side+i-1)
 end
 g.collected=update_collected(
  prvc,dice
 )

 set_game_animation(g,moving)

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

 game=g
 poke(a_ctrl_in_game,0)
end

--show client joins/leaves in
--chat log
function log_client_changes(
 old,new
)
 for id,name in pairs(old) do
  if new[id]==nil then
   add_chat(
    room.chatlog,id,name,"-"
   )
  end
 end

 for id,name in pairs(new) do
  if old[id]==nil and id!=1 then
   add_chat(
    room.chatlog,id,name,"+"
   )
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
  room.host=r.host
  roomnew=nil
 end

 poke(a_ctrl_in_room,0)
end

function read_gpio_chat()
 if peek(a_chat_in_msg)==0 then
  return
 end

 add_chat(
  room.chatlog,
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

function animation_update()
 if (animate) animate.update()
end

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

function game_chat()
 if btnp(⬅️) or btnp(➡️) then
  room.chatidx=0
 elseif btnp(⬆️) then
  room.chatidx=(
   room.chatidx+#chatmsg-2
  )%#chatmsg+1
 elseif btnp(⬇️) then
  room.chatidx=(
   room.chatidx%#chatmsg+1
  )
 elseif room.chatidx!=0
 and actionbtnp() then
  poke(
   a_chat_out_msg,room.chatidx
  )
  room.chatidx=0
  
  --signal that action button
  --was handled by chat to
  --avoid that it also triggers
  --a game action
  return true
 end

 room.chat_active=(
  room.chatidx!=0
 )
end

function game_update()
 read_gpio()

 if game.winner then
  animate_endgame()
 end
 
 if not game_chat() then
  if game.pickdie then
   game_pickdie()
  elseif game.chkpass then
   game_chkpass()
  end
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

 animation_update()
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

 if room.help42 then
  room.help42-=1
  if room.help42==0 then
   room.help42=nil
  end
 end

 room.chat_active=(
  room.ypos==3
 )
 
 if actionbtnp() then
  if room.ypos==1 then
   if room.host==1 then
    --initiate game start
    poke(a_ctrl_in_game,5)
   else
    show_popup_msg(
     "only the host can start a game"
    )
   end
  elseif room.ypos==2 then
   if room.help!=nil then
    room.help=nil
   elseif room.help42 then
    show_popup_msg("don't panic")
   else
    room.help=0
    room.help42=30
    room.helpdelta=0
   end
  elseif room.ypos==3 then
   if room.chatidx!=0 then
    poke(
     a_chat_out_msg,room.chatidx
    )
    room.chatidx=0
   else
    show_popup_msg(
     "select message using ⬆️ and ⬇️"
    )
   end
  elseif room.ypos==4
  and peek(a_room_mgmt)==3 then
   --initiate room exit
   poke(a_room_mgmt,4)
  end
 end

 read_gpio()
 title_update()
 animation_update()
end

function enter_room(room_id)
 if room_id!=nil then
  room.id=room_id
  room.chatlog={}
 end

 room.ypos=1
 room.chatidx=0
 room.help=nil
 room.error=nil
 title.room=room_id
 title_init_earthlings(0)

 poke(a_chat_in_msg,0)
 poke(a_chat_out_msg,0)

 --clear game status
 game=nil
 animate=nil
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

 show_popup_msg(
  "joining room "..room_id
 )

 --initiate join
 poke(a_room_mgmt,1)
end

function create_room()
 clear_room_status()

 gpio_puts(a_name,6,menu.name)

 show_popup_msg(
  "creating room..."
 )

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
 end
end

function title_init_earthlings(
 n
)
 local l={}
 for i=1,n do
  add(l,{
   tp=3+i%3,x=60,y=112,dx=0
  })
 end
 title.earthlings=l
end

function title_update()
 --move flying saucers
 for i=1,2 do
  if rnd(10)<1 then
   local d=title.delta[i]
   local v=vector[flr(rnd(4))+1]
   for j=1,2 do
    d[j]=max(min(d[j]+v[j],1),-1)
   end
  end
 end

 --move earthlings
 for e in all(title.earthlings) do
  if e.y==112 then
   if e.dx==0 and rnd(1)<0.1 then
    e.dx=flr(rnd(2))*2-1
    e.flip=e.dx>0
   end
   if e.dx!=0 and rnd(1)<0.1 then
    e.dx=0
   end
   
   e.x+=e.dx
   if e.x<9 or e.x>103 then
    e.y-=1
   end
  else
   if e.y>0 then
    e.y-=1
   else
    e.x=64
    e.y=112
    e.dx=0
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
   show_popup_msg(
    "error: "..msg
   )
  else
   show_popup_msg(
    "error: "..peek(a_errr)
   )
  end
  poke(a_room_mgmt,0)
 end

 if menu.xpos!=0 then
  menu_edittext()
 else
  menu_itemselect()
 end

 title_update()
 animation_update() 
end

function show_menu()
 _draw=menu_draw
 _update=menu_update

 if (menu.ypos==4) title.room=""

 title_init_earthlings(3)
end

function qr_update()
 title_update()
 if peek(a_handshke)==8 then
  show_menu()
 end
end

function show_qr()
 poke(a_handshke,7)

 _draw=qr_draw
 _update=qr_update
 title_init_earthlings(3)
end

function intro_update()
 animation_update()
 if (animate==nil) show_qr()
end

function show_intro()
 animate_intro()

 _draw=intro_draw
 _update=intro_update
end

-->8
function dev_init_game()
 local t0=new_throw(
  {2,2,2,1,1}
 )
 local moving={}
 local t1=update_throw(
  t0,{2,0,2,1,1},moving
 )
 local b0=update_battle(
  {},{1,0}
 )
 local b1=update_battle(
  b0,{1,2}
 )
 animate_move(b0,b1,moving)
 game={
  throw=t1,
  battle=b1,
  collected=update_collected(
   {},{[4]=2}
  ),
  round=1,
  turn=2,
  phase=phase.pickdice,
  thrownum=3,
  endcause=0,
  active_player={
   name="me",
   avatar=32,
   color=pal1[1]
  }
 }
 --game.pickdie=die_choices(game)
 game.die_idx=1
 --game.chkpass=true
 --game.pass=false
 --animate_game_throw(game.throw)

 if false then
  game.endcause=1
  game.scored=2
  game.score=2
  game.position=1
 end
 if false then
  game.score=27
  game.winner=game.active_player
  game.phase=phase.endgame
  animate_endgame()
 end
 cls()

 local log={}
 add_chat(log,2,"hi")
 add_chat(log,3,"hi")
 room={
  chatlog=log,
  chatidx=0
 }

 _update=game_update
 _draw=game_draw
 poke(a_ctrl_out,0)
 poke(a_room_mgmt,3)
end

function dev_init_room()
 local log={}
 add_chat(log,2,"hi")
 add_chat(log,3,"hi")

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
  chatlog=log
 }
 title.room="pico"
 title.public=true

 _update=room_update
 _draw=room_draw
 poke(a_room_mgmt,3)
end

function _init()
 show_intro()

 --show_qr()

 --poke(a_room_mgmt,0)
 --show_menu()

 --dev_init_game()
 
 --dev_init_room()

 --_draw=draw_all_help()
 --_update=function() end
end

__gfx__
00000000bbbbbbb000000000e9eeeeeee0000000000000eee0000000000000eee0000000000000eee0000000000000eee0000000000000ee0000000000000000
00000000b00000b000000080e99eeeee000000000000000e000000000000000e0000000aa000000e000000000000000e000000000000000e0000000000000000
00700700b0bbb0b088888888ee99eeee000000000000000e000000000000000e000000a00a00000e007770777077700e00000ccccc00000e0000000000000000
00077000b0bbb0b008800080eee99eee000000000000000e000000000000000e000aa0aaaa0aa00e007007000700700e0000c00000c0000e0000000000000000
00077000b0bbb0b008800000eeee99ee000000bbb000000e000000888008800e00a00a0000a00a0e000770000077000e000c0000000c000e0000000000000000
007007000b0b0b0088000000eeeee99e00000b000b00000e000008000880000e00a0a000000a0a0e000070707070000e00c00c000c00c00e0000000000000000
000000000bb0bb0088000000eeee99ee00000b000b00000e000008888800000e000a00000000a00e000070707070000e00c00c000c00c00e0000000000000000
0000000000bbb00000000000eee99eee00bbbbbbbbbbb00e008888888888800e000a0a000000a00e000070000070000e00c000000000c00e0000000000000000
00cccc0007777770aa00a0aaee99ee9e0b00000000000b0e080000000000080e00aa00000000a00e000077777770000e00c0c00000c0c00e0000000000000000
0cccccc077777777aaaa00aae99ee99e0b00000000000b0e080800000008080e0aaa00000000a00e000700000007000e00c00c000c00c00e0000000000000000
cc0cc0cc7707707700000a00e9ee99ee0b00000000000b0e080000000000080e0000a000000a000e007000707000700e000c00ccc00c000e0000000000000000
cc0cc0cc7777777700a0a00aeee99eee00bbbbbbbbbbb00e008888888888800e00000a0000a0000e007000000000700e0000c00000c0000e0000000000000000
cccccccc7777777700a0a0a0ee99eeee000000000000000e000000000000000e000000aaaa00000e000700000007000e00000ccccc00000e0000000000000000
cc0cc0cc7707707700a0a0a0e99eeeee000000000000000e000000000000000e000000000000000e000077777770000e000000000000000e0000000000000000
0cc00cc077777777aa00a0aae9eeeeeee0000000000000eee0000000000000eee0000000000000eee0000000000000eee0000000000000ee0000000000000000
00cccc0007777770aa00a0aaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee0000000000000000
0ccc0000ddddd00002220000ff0ff00006660000330330001111111e1111111e1111111e1a1a1a1e1711171e11ccc11e00000000000000000000000000000000
c0c0c00000d000002020200000f00000006000003303300011bbb11e11bbb11e8888811e11aaa11e1777771e1ccccc1e00000000000000000000000000000000
ccccc000ddddd0002222200000f00000606060000030000011bbb11e11bbb11e1188811e1a1aaa1e1717171ecc1c1cce00000000000000000000000000000000
c000c000d000d00022022000f000f0006000600030003000bbbbbbbebbbbbbbe8888888e1aaaaa1e1717171eccccccce00000000000000000000000000000000
0ccc00000ddd0000222220000fff00000666000003330000bbbbbbbebbbbbbbe8888888eaaaaaa1e7777777ec1ccc1ce00000000000000000000000000000000
0000000000000000000000000000000000000000000000001111111e1111111e1888881e11aaa11e7717177e1c111c1e00000000000000000000000000000000
0000000000000000000000000000000000000000000000001111111e1111111e1111111e1111111e1777771e11ccc11e00000000000000000000000000000000
000000000000000000000000000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000
77777770007777007777700088888000bbbbb000aaaa000000000400000000004444400000000000000000000000000000000000000000000000000000000000
70000070077777707070700088888000bbbbb000000aa00000004940000000004440000000000000000000000000000000000000000000000000000000000000
70777070770770777777700008800000bbbbb000aa0aa00004444494000000004400000000000000000000000000000000000000000000000000000000000000
707770707707707770707000880000000bbb0000aa00000049999999400000004000000000000000000000000000000000000000000000000000000000000000
7077707077777777777770008800000000b000000aaaa00004444494000000004000000000000000000000000000000000000000000000000000000000000000
07070700770770770000000000000000000000000000000000004940000000000000000000000000000000000000000000000000000000000000000000000000
07707700077007700000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000000000000000
00777000007777000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
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
eeeeee0eeeeeee0eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeee040eeeee040eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeee0440eee0440eeeeeeeeeeeeeeeeeeeeeeeeeeeee00eeeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeee04440e04440eeeeeee0eeeeeeeeeeeeeeeeeeee0440eeeee0eeeeee0eeeee0eeeee00000000000000000000000000000000000000000000000000000000
eeee0444440444440eeeee040eeeeeeeeeeeeeeeeeee0440eeee040eeee040eee040eeee00000000000000000000000000000000000000000000000000000000
eeee0440444440440eeeee040ee0000000ee000000000000eeee040eeee040eee040eeee00000000000000000000000000000000000000000000000000000000
eeee0440444440440eeee0444004444444004444444444440ee04440eee0440e0440eeee00000000000000000000000000000000000000000000000000000000
eeee0440044400440eeee04440e004444440004444440000eee04440eee0440e0440eeee00000000000000000000000000000000000000000000000000000000
eee044400444004440eee04040eee04400440e0044000440eee04040eee044400440eeee00000000000000000000000000000000000000000000000000000000
eee04440e040e04440ee0440440ee04400440ee0440e0440ee0440440ee044400440eeee00000000000000000000000000000000000000000000000000000000
eee04440e040e04440ee040e040ee04400440ee0440e0440ee040e040ee044440440eeee00000000000000000000000000000000000000000000000000000000
eee04440e040e04440e044000440e0444440eee0440e0440e044000440e044040440eeee00000000000000000000000000000000000000000000000000000000
eee04440e040e04440e044444440e0444440eee0440e0440e044444440e044044440eeee00000000000000000000000000000000000000000000000000000000
eee04440ee0ee04440e044000440e0440040eee0440e0440e044000440e044004440eeee00000000000000000000000000000000000000000000000000000000
eee04440eeeee04440e0440e0440e04400440ee0440e0440e0440e0440e044004440eeee00000000000000000000000000000000000000000000000000000000
eee04440eeeee04440e0440e0440e04400440e044440444400440e0440e0440e0440eeee00000000000000000000000000000000000000000000000000000000
ee0444440eee04444404440e04440444004440044440444404440e044404440e04440eee00000000000000000000000000000000000000000000000000000000
eee00000eeeee00000e000eee000e000ee000ee0000e0000e000eee000e000eee000eeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeeee000000ee0000ee000000ee000000eeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeee044444400444400444444004444440eeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeee00044444004400444440004444400eeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeee04400004440440444000e0444000eeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeee0440ee0440440440eeee04400eeeeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeee0440ee0440440440eeee0444400eeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeee0440ee0440440440eeee04444440eeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeee0440ee0440440440eeee0444400eeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeee0440ee0440440440eeee04400eeeeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeee04400004440440444000e0444000eeeeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeee00044444004400444440004444400eeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeee044444400444400444444004444440eeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeeee000000ee0000ee000000ee000000eeeeeeeeeeeeeeeeeeeeee00000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e00000007000000700770770000000ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07777707070707770007770777770ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07000707700070007777770700070ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07000707000777077077070700070ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07000707700707007070770700070ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07777707770070077770770777770ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e00000007070707070707070000000ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e77777777000077007007077777777ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07007000777707777007070770700ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07700777007770770000000007770ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e70700700777707770007000707007ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e77700070077070077777000777770ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07000707007077007070777070077ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07070777770007700770070777000ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e00777000700000777700070707000ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07077070077007700707077077707ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e00777700700770007777077000707ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e77707077000077007077077070007ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07000700707077700077070077077ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e77700777700777077077770707077ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e70000700700770770007000000077ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e77777777070700770007077700000ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e00000007000000770700070700707ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07777707077707707777077700700ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07000707700707007077000007000ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07000707070707070770707000770ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07000707070707777707077077070ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e07777707707000770707000770707ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
e00000007007777707770077077707ee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
__label__
44444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444
44444444000000000000000000000000000000000004444444444444444444444444444444444444444440000000000000000000000000000000000044444444
44444400000000000000000000000000000000000000044444444444444444444444444444444444444000000000000000000000000000000000000000444444
44444000000000000000000000000000000000000000004444444444444444444444444444444444440000000000000000000000000000000000000000044444
44440000000000000000000000000000000000000000000444444444444444444444444444444444400000000000000000000000000000000000000000004444
44440000000000000000000000000000000000000000000444444444444444444444444444444444400000000000000000000000000000000000000000004444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44400000000000000000088888888800000088888800000044444444444444444444444444444444000000000000000000bbbbbbbbb000000000000000000444
44400000000000000000088888888800000088888800000044444444444444444444444444444444000000000000000000bbbbbbbbb000000000000000000444
44400000000000000000088888888800000088888800000044444444444444444444444444444444000000000000000000bbbbbbbbb000000000000000000444
44400000000000000088800000000088888800000000000044444444444444444444444444444444000000000000000bbb000000000bbb000000000000000444
44400000000000000088800000000088888800000000000044444444444444444444444444444444000000000000000bbb000000000bbb000000000000000444
44400000000000000088800000000088888800000000000044444444444444444444444444444444000000000000000bbb000000000bbb000000000000000444
44400000000000000088888888888888800000000000000044444444444444444444444444444444000000000000000bbb000000000bbb000000000000000444
44400000000000000088888888888888800000000000000044444444444444444444444444444444000000000000000bbb000000000bbb000000000000000444
44400000000000000088888888888888800000000000000044444444444444444444444444444444000000000000000bbb000000000bbb000000000000000444
44400000088888888888888888888888888888888800000044444444444444444444444444444444000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb000000444
44400000088888888888888888888888888888888800000044444444444444444444444444444444000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb000000444
44400000088888888888888888888888888888888800000044444444444444444444444444444444000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb000000444
44400088800000000000000000000000000000000088800044444444444444444444444444444444000bbb000000000000000000000000000000000bbb000444
44400088800000000000000000000000000000000088800044444444444444444444444444444444000bbb000000000000000000000000000000000bbb000444
44400088800000000000000000000000000000000088800044444444444444444444444444444444000bbb000000000000000000000000000000000bbb000444
44400088800088800000000000000000000088800088800044444444444444444444444444444444000bbb000000000000000000000000000000000bbb000444
44400088800088800000000000000000000088800088800044444444444444444444444444444444000bbb000000000000000000000000000000000bbb000444
44400088800088800000000000000000000088800088800044444444444444444444444444444444000bbb000000000000000000000000000000000bbb000444
44400088800000000000000000000000000000000088800044444444444444444444444444444444000bbb000000000000000000000000000000000bbb000444
44400088800000000000000000000000000000000088800044444444444444444444444444444444000bbb000000000000000000000000000000000bbb000444
44400088800000000000000000000000000000000088800044444444444444444444444444444444000bbb000000000000000000000000000000000bbb000444
44400000088888888888888888888888888888888800000044444444444444444444444444444444000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb000000444
44400000088888888888888888888888888888888800000044444444444444444444444444444444000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb000000444
44400000088888888888888888888888888888888800000044444444444444444444444444444444000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb000000444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44440000000000000000000000000000000000000000000444444444444444444444444444444444400000000000000000000000000000000000000000004444
44440000000000000000000000000000000000000000000444444444444444444444444444444444400000000000000000000000000000000000000000004444
44444000000000000000000000000000000000000000004444444444444444444444444444444444440000000000000000000000000000000000000000044444
44444400000000000000000000000000000000000000044444444444444444444444444444444444444000000000000000000000000000000000000000444444
44444444000000000000000000000000000000000004444444444444444444444444444444444444444440000000000000000000000000000000000044444444
44444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444044444440444444444444444444444444444444444444444444444444444444444444444444444444444444444444
44444444444444444444444444444444440904444409044444444444444444444444444444444444444444444444444444444444444444444444444444444444
44444444444444444444444444444444440990444099044444444444444444444444444444004444444444444444444444444444444444444444444444444444
44444444444444444444444444444444440999040999044444440444444444444444444440990444440444444044444044444444444444444444444444444444
44444444444444444444444444444444409999909999904444409044444444444444444440990444409044440904440904444444444444444444444444444444
44444444444444444444444444444444409909999909904444409044000000044000000000000444409044440904440904444444444444444444444444444444
44444444444444444444444444444444409909999909904444099900999999900999999999999044099904440990409904444444444444444444444444444444
44444444444444444444444444444444409900999009904444099904009999990009999990000444099904440990409904444444444444444444444444444444
44444444444444444444444444444444099900999009990444090904440990099040099000990444090904440999009904444444444444444444444444444444
44444444444444444444444444444444099904090409990440990990440990099044099040990440990990440999009904444444444444444444444444444444
44444444444444444444444444444444099904090409990440904090440990099044099040990440904090440999909904444444444444444444444444444444
44444444444444444444444444444444099904090409990409900099040999990444099040990409900099040990909904444444444444444444444444444444
44444444444444444444444444444444099904090409990409999999040999990444099040990409999999040990999904444444444444444444444444444444
44444444444444444444444444444444099904404409990409900099040990090444099040990409900099040990099904444444444444444444444444444444
44444444444444444444444444444444099904444409990409904099040990099044099040990409904099040990099904444444444444444444444444444444
44444444444444444444444444444444099904444409990409904099040990099040999909999009904099040990409904444444444444444444444444444444
44444444444444444444444444444440999990444099999099904099909990099900999909999099904099909990409990444444444444444444444444444444
44444444444444444444444444444444000004444400000400044400040004400044000040000400044400040004440004444444444444444444444444444444
44444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444400000044000044000000440000004444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444099999900999900999999009999990444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444000999990099009999900099999004444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444440990000999099099900040999000444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444099044099099099044440990044444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444099044099099099044440999900444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444099044099099099044440999999044444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444099044099099099044440999900444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444099044099099099044440990044444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444440990000999099099900040999000444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444000999990099009999900099999004444444444444444444444444444444444444444444444444
44444444000000000000000000000000000000000004444444099999900999900999999009999990444440000000000000000000000000000000000044444444
44444400000000000000000000000000000000000000044444400000044000044000000440000004444000000000000000000000000000000000000000444444
44444000000000000000000000000000000000000000004444444444444444444444444444444444440000000000000000000000000000000000000000044444
44440000000000000000000000000000000000000000000444444444444444444444444444444444400000000000000000000aaaaaa000000000000000004444
44440000000000000000000000000000000000000000000444444444444444444444444444444444400000000000000000000aaaaaa000000000000000004444
44400000000000000000000000000000000000000000000044444444444444444444444444444444000000000000000000000aaaaaa000000000000000000444
44400000077777777700077777777700077777777700000044444444444444444444444444444444000000000000000000aaa000000aaa000000000000000444
44400000077777777700077777777700077777777700000044444444444444444444444444444444000000000000000000aaa000000aaa000000000000000444
44400000077777777700077777777700077777777700000044444444444444444444444444444444000000000000000000aaa000000aaa000000000000000444
44400000077700000077700000000077700000077700000044444444444444444444444444444444000000000aaaaaa000aaaaaaaaaaaa000aaaaaa000000444
44400000077700000077700000000077700000077700000044444444444444444444444444444444000000000aaaaaa000aaaaaaaaaaaa000aaaaaa000000444
44400000077700000077700000000077700000077700000044444444444444444444444444444444000000000aaaaaa000aaaaaaaaaaaa000aaaaaa000000444
44400000000077777700000000000000077777700000000044444444444444444444444444444444000000aaa000000aaa000000000000aaa000000aaa000444
44400000000077777700000000000000077777700000000044444444444444444444444444444444000000aaa000000aaa000000000000aaa000000aaa000444
44400000000077777700000000000000077777700000000044444444444444444444444444444444000000aaa000000aaa000000000000aaa000000aaa000444
44400000000000077700077700077700077700000000000044444444444444444444444444444444000000aaa000aaa000000000000000000aaa000aaa000444
44400000000000077700077700077700077700000000000044444444444444444444444444444444000000aaa000aaa000000000000000000aaa000aaa000444
44400000000000077700077700077700077700000000000044444444444444444444444444444444000000aaa000aaa000000000000000000aaa000aaa000444
44400000000000077700077700077700077700000000000044444444444444444444444444444444000000000aaa000000000000000000000000aaa000000444
44400000000000077700077700077700077700000000000044444444444444444444444444444444000000000aaa000000000000000000000000aaa000000444
44400000000000077700077700077700077700000000000044444444444444444444444444444444000000000aaa000000000000000000000000aaa000000444
44400000000000077700000000000000077700000000000044444444444444444444444444444444000000000aaa000aaa000000000000000000aaa000000444
44400000000000077700000000000000077700000000000044444444444444444444444444444444000000000aaa000aaa000000000000000000aaa000000444
44400000000000077700000000000000077700000000000044444444444444444444444444444444000000000aaa000aaa000000000000000000aaa000000444
44400000000000077777777777777777777700000000000044444444444444444444444444444444000000aaaaaa000000000000000000000000aaa000000444
44400000000000077777777777777777777700000000000044444444444444444444444444444444000000aaaaaa000000000000000000000000aaa000000444
44400000000000077777777777777777777700000000000044444444444444444444444444444444000000aaaaaa000000000000000000000000aaa000000444
44400000000077700000000000000000000077700000000044444444444444444444444444444444000aaaaaaaaa000000000000000000000000aaa000000444
44400000000077700000000000000000000077700000000044444444444444444444444444444444000aaaaaaaaa000000000000000000000000aaa000000444
44400000000077700000000000000000000077700000000044444444444444444444444444444444000aaaaaaaaa000000000000000000000000aaa000000444
44400000077700000000077700077700000000077700000044444444444444444444444444444444000000000000aaa000000000000000000aaa000000000444
44400000077700000000077700077700000000077700000044444444444444444444444444444444000000000000aaa000000000000000000aaa000000000444
44400000077700000000077700077700000000077700000044444444444444444444444444444444000000000000aaa000000000000000000aaa000000000444
44400000077700000000000000000000000000077700000044444444444444444444444444444444000000000000000aaa000000000000aaa000000000000444
44400000077700000000000000000000000000077700000044444444444444444444444444444444000000000000000aaa000000000000aaa000000000000444
44400000077700000000000000000000000000077700000044444444444444444444444444444444000000000000000aaa000000000000aaa000000000000444
44400000000077700000000000000000000077700000000044444444444444444444444444444444000000000000000000aaaaaaaaaaaa000000000000000444
44400000000077700000000000000000000077700000000044444444444444444444444444444444000000000000000000aaaaaaaaaaaa000000000000000444
44400000000077700000000000000000000077700000000044444444444444444444444444444444000000000000000000aaaaaaaaaaaa000000000000000444
44400000000000077777777777777777777700000000000044444444444444444444444444444444000000000000000000000000000000000000000000000444
44440000000000077777777777777777777700000000000444444444444444444444444444444444400000000000000000000000000000000000000000004444
44440000000000077777777777777777777700000000000444444444444444444444444444444444400000000000000000000000000000000000000000004444
44444000000000000000000000000000000000000000004444444444444444444444444444444444440000000000000000000000000000000000000000044444
44444400000000000000000000000000000000000000044444444444444444444444444444444444444000000000000000000000000000000000000000444444
44444444000000000000000000000000000000000004444444444444444444444444444444444444444440000000000000000000000000000000000044444444
44444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444
44444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444444

__map__
00000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
__sfx__
000100001d05000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
000200001a05000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
