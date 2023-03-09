# Tomato

Tomato 是一个日程管理软件。

## 解决问题

目前，macOS 的 Reminders 和 Calendar 在处理日程安排时存在以下问题：

1. Reminders 和 Calendar 软件并立，数据不联通、视图不通用，经常出现冲突的时间安排。

   早在 21 世纪 10 年代之初或者更早，就有帖子希望将 Reminders 和 Calendar 两个软件合二为一。当然，Apple 至今没有这样改变的原因我们不得而知，可能因为这两个软件仍然有功能上的分野——例如 Reminders 更多地是提醒服务，主要适用于重复性的工作，尤其是时间敏感（time sensitive）的子项，而 Calendar 更多地是展现固定事项，以日历的形式平铺待办事项。可是，如果两个数据库并不统一，那么很可能出现两件事项矛盾冲突的情形，也无法以对统一的事项使用不同的视图，而如果想要为同一件事设定安排，则需要分别在两个软件内添加。

2. 没有记录功能。

   Reminders 和 Calendar 没有记录功能，只有计划和安排，而记录则需要手动复制粘贴，无法自动无感知记录。当用户不能记忆自己的行为，尤其是行为的时间时，记录就是一项高成本的工作。

3. 对不同类型的日程没有明确分类。

   Reminders 提供“时间敏感”（time sensitive）和频率敏感（frequency sensitive）的提醒服务，而 Calendar 只能设定前者，且这一功能特性并未显明地放在首位。如果用户有一些想放入日程安排的想法或者想要区分不同的类型，又或者对某一个想法只有一个模糊的时间印象，那么 Reminders 或者 Calendar 都无法用来记录这类信息。

如果你对 macOS 上原生日程管理工具有如上思考，或许你可以考虑用一下 Tomato 来管理你的个人事项。

## 功能亮点

1. 数据自有，本地优先。

   Tomato 不会隐藏任何数据的存储数据，无论何时，你都可以前往用户的根目录查看 TomatoAppPath 这一文件夹，所有的计划项目都存放在 All.csv 文件中，日记文件存放在 Diary 文件夹中，所有事项的记录存放于 Record 文件夹中。同样，用户任何时候都可以从 Tomato 的界面上选择导出上述三种文件于电脑的任意位置。

2. 把 Reminder 和 Calendar 的功能结合起来，联动响应。

   Tomato 提供了一个基于 Reminders 和 Calendar 的统一控制平台，无论是添加日程，抑或是完成日程、删除日程，都可以方便地实现，一次操作可同时命令两个软件。

3. 以表格形式展现换管理日程。

   目前，Calendar 和 Reminder 都使用的是层层套叠的形式。为了简洁明了，macOS 将大量功能隐藏在点按拖拽的背后，虽然形式上更好看，但操作起来更不直观，获取信息也需要多次点击。Tomato 以更传统、更经典和更直白的数据库形式排列日程，使你所有的信息和功能都可以轻松点击，所见即所得。

4. 结合日程安排与日记、工作记录，计算支持周报（AI）功能

## 下载安装

1. **下载**：在 Release 或者 compiled 文件夹里面找到最新的版本，下载，将解压的 .app 软件放入程序文件夹（Application）中。

2. **打开**：在文件夹或者 launchpad 中双击打开，会弹出如下弹窗，请选择“打开”。

     <p align="center">
       <img src="https://i.imgur.com/K4ffys4.png" width=240 />
     </p>

3. **权限**：Tomato 需要三种权限。

  - 辅助功能权限：Tomato 会请求用户的 Accessiblity 权限，请允许。Tomato 完全是一个本地软件，不会上传任何关于您的数据。

  - 读取数据权限：Tomato 需要在您的电脑中存放数据，并将这些数据存储在 Reminders 和 Calendar 中。请在弹出的这两个窗口中选择“OK”。

    <p align="center">
      <img src="https://i.imgur.com/vjZqKmy.png" width=240 />
      <img src="https://i.imgur.com/boeUagz.png" width=240 />
    </p>

  - 控制软件权限：要实现对 Reminders 和 Calendar 两个软件的同步和联动控制，Tomato 就需要获得修改这两个软件数据的权限。请在弹出的对“System Events”、“Reminders”和“Calendar”三个弹窗内点击“OK”。

    <p align="center">
      <img src="https://i.imgur.com/yBtyDFz.png" width=240 />
      <img src="https://i.imgur.com/6iDLBOl.png" width=240 />
      <img src="https://i.imgur.com/fmNI87a.png" width=240 />
    </p>
    
    
    

## 功能运用



## 支持作者

<p align="center">
  <img src="https://i.imgur.com/OHHJD4y.png" width=240 />
  <img src="https://i.imgur.com/6XiKMAK.png" width=240 />
</p>
