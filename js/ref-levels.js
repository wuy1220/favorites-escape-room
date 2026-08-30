/* 范例关卡数据:designWindow(范例模仿设计师)的 few-shot 素材。
   2026-08-29 瘦身版:scenes 双房间紧凑结构(压缩 tokens 以满足 160s 生成预算),
   保留教学核心:谜题链(result:/resultOn/consume)、机关推导(事实锚定)、reason 交叉、
   hidden 容器显形、theme/creativeThesis 创作计划。
   由 pipeline.js 在运行时引用:const REF_LEVELS=window.__REF_LEVELS__; */
window.__REF_LEVELS__ = [
  {
    "title": "监狱（原作第二关复刻）",
    "theme": "破败牢房——铁锈、潮气与勉强还在转的旧机械",
    "adventureGrammar": "变形:每件工具使用后变成下一件,最终拼出完整的逃脱钥匙",
    "creativeThesis": "每件被收藏的工具，都是一次未完成的越狱。",
    "recurringMotif": "转动的机械（转盘、锯齿、指纹锁）",
    "surpriseTurn": "无",
    "premise": "你在牢房墙角醒来，脚被镣铐锁住。房间里散落着工具与锁具。",
    "objective": "拿到锯子做成棍子，勾下钥匙解开镣铐；通电电报台敲出摩斯码，打开大铁箱按指纹开门。",
    "targetMinutes": 12,
    "mechanics": ["铁箱密码 685 = 摩斯对照(3=...--,7=--...) + 日记生日 3月14日 的 14"],
    "hints": [
      "转盘锁刻着「时针三点、分针六点」，换算成角度。",
      "锯断排水管做成棍子，勾下墙上的钥匙。",
      "笔记是摩斯对照表，日记写着生日 3 月 14 日。",
      "大铁箱密码 = 摩斯码数字 + 生日数字的组合。"
    ],
    "scenes": [
      {
        "id": "pr-wall",
        "title": "牢房墙角",
        "description": "墙角立着上锁的铁柜，排水管从墙里伸出。",
        "focus": "上锁的铁柜",
        "items": [
          { "id": "pr-dial", "role": "lock", "sceneName": "转盘锁", "reason": "锁面刻着：时针三点，分针六点。" },
          { "id": "pr-saw", "role": "tool", "sceneName": "锯子", "reason": "柜中锯子，锯齿锋利。", "hidden": true },
          { "id": "pr-pipe", "role": "tool", "sceneName": "排水管", "reason": "金属管，可锯断。" },
          { "id": "pr-key", "role": "lock", "sceneName": "墙上的钥匙", "reason": "挂在高处，需要长棍勾取。" },
          { "id": "pr-shackle", "role": "lock", "sceneName": "镣铐", "reason": "锁住你的脚，需要钥匙。" }
        ],
        "beats": [
          { "id": "b-angle", "title": "打开转盘锁", "action": "angle", "uses": ["pr-dial"], "reveals": ["pr-saw"], "product": "打开的转盘锁", "angles": [90, 180], "precision": 30 },
          { "id": "b-saw-pipe", "title": "锯断排水管", "action": "combine", "uses": ["pr-saw", "pr-pipe"], "requires": ["b-angle"], "product": "棍子" },
          { "id": "b-get-key", "title": "勾下钥匙", "action": "combine", "uses": ["result:b-saw-pipe", "pr-key"], "requires": ["b-saw-pipe"], "product": "钥匙" },
          { "id": "b-unlock", "title": "解开镣铐", "action": "combine", "uses": ["result:b-get-key", "pr-shackle"], "requires": ["b-get-key"], "resultOn": "pr-shackle", "product": "解开的镣铐" }
        ]
      },
      {
        "id": "pr-desk",
        "title": "电报室",
        "description": "里间的电报台空着电池槽，台面上有笔记与日记；门边是密码铁箱与指纹锁。",
        "focus": "没有电池的电报机",
        "items": [
          { "id": "pr-battery", "role": "tool", "sceneName": "电池", "reason": "夹在日记本书页间的旧电池，电量还足。", "hidden": true },
          { "id": "pr-telegraph", "role": "tool", "sceneName": "电报机", "reason": "台面上的老式电报机，电池槽空着——装上电池才能敲码。" },
          { "id": "pr-note", "role": "clue", "sceneName": "笔记", "reason": "摩斯对照表：3 是 ...--，7 是 --...。" },
          { "id": "pr-diary", "role": "clue", "sceneName": "日记本", "reason": "最后一页写着：生日 3 月 14 日。书页间还夹着什么东西。" },
          { "id": "pr-chest", "role": "lock", "sceneName": "密码铁箱", "reason": "箱面刻着：电报机的数字与生日数字相加。" },
          { "id": "pr-fp-lock", "role": "lock", "sceneName": "指纹锁", "reason": "门上的指纹锁，需要一枚完整手指。" }
        ],
        "beats": [
          { "id": "b-power", "title": "装电池", "action": "combine", "uses": ["pr-battery", "pr-telegraph"], "requires": ["b-read"], "resultOn": "pr-telegraph", "product": "通电的电报机" },
          { "id": "b-read", "title": "读笔记和日记", "action": "inspect", "uses": ["pr-diary", "pr-note"], "reveals": ["pr-battery"] },
          { "id": "b-morse", "title": "输入摩斯码", "action": "morse", "uses": ["result:b-power"], "requires": ["b-read"], "product": "记下密码的电报机", "code": "...--/--.../.----" },
          { "id": "b-chest", "title": "打开铁箱", "action": "password", "uses": ["pr-chest"], "expected": "685", "requires": ["b-morse"], "product": "打开的铁箱" },
          { "id": "b-finger", "title": "按指纹锁", "action": "combine", "uses": ["pr-fp-lock", "pr-telegraph"], "resultOn": "pr-fp-lock", "requires": ["b-chest", "b-unlock"], "product": "解锁的指纹锁" },
          { "id": "b-escape", "title": "从出口离开", "action": "deliver", "uses": ["result:b-finger"], "requires": ["b-finger"] }
        ]
      }
    ]
  },
  {
    "title": "深夜情报 · 熊曰",
    "theme": "深夜书桌——一盏台灯、旧纸与嗡嗡作响的解密终端",
    "adventureGrammar": "无中心选集:便签与工具说明各自成对,结局才暴露它们共享的密文规则",
    "creativeThesis": "随手存下的解密工具，终将成为打开自己秘密的钥匙。",
    "recurringMotif": "倒序（倒着读的字、倒放的磁带）",
    "surpriseTurn": "无",
    "premise": "你醒在书桌前，手边一张擦花便签开头认出『呋』字——那是熊曰密文的标头。",
    "objective": "用铅笔擦出便签密文，读工具说明学会解密规则，在解密终端输入密码，拿回钥匙打开地址栏。",
    "targetMinutes": 10,
    "mechanics": ["终端密码 246 = 便签密文『和既很』倒序 → 熊字表换数字（很2 既4 和6）"],
    "hints": [
      "铅笔涂在便签上，字迹会现形。",
      "密文要先倒过来读，再按熊字表换数字。",
      "字典节选：很2 既4 和6。"
    ],
    "scenes": [
      {
        "id": "bd-desk",
        "title": "深夜书桌",
        "description": "台灯下压着擦花的便签，旁边是铅笔和工具说明。",
        "focus": "被擦花的便签",
        "items": [
          { "id": "bd-note", "role": "clue", "sceneName": "加密便签", "reason": "开头认出『呋』字——熊曰密文的标头。便签下面还压着东西。" },
          { "id": "bd-pencil", "role": "tool", "sceneName": "铅笔", "reason": "压在便签下面的铅笔，涂在擦花处字迹会现形。", "hidden": true },
          { "id": "bd-bear", "role": "clue", "sceneName": "与熊论道", "reason": "密文倒序后按熊字表换数字。节选：很2 既4 和6。" }
        ],
        "beats": [
          { "id": "b-note", "title": "读加密便签", "action": "inspect", "uses": ["bd-note"], "reveals": ["bd-pencil"] },
          { "id": "b-bear", "title": "读工具说明", "action": "inspect", "uses": ["bd-bear"] },
          { "id": "b-reveal", "title": "擦出字迹", "action": "combine", "uses": ["bd-pencil", "bd-note"], "requires": ["b-note", "b-bear"], "resultOn": "bd-note", "product": "显出字迹的情报" }
        ]
      },
      {
        "id": "bd-terminal",
        "title": "终端里间",
        "description": "里间的解密终端亮着待机屏，旁边立着地址栏锁具。",
        "focus": "解密终端",
        "items": [
          { "id": "bd-term", "role": "lock", "sceneName": "解密终端", "reason": "需输入三位数字。提示：倒过来读，再按熊字表换数。" },
          { "id": "bd-key", "role": "reward", "sceneName": "钥匙", "reason": "情报解出后终端滑出的钥匙。", "hidden": true },
          { "id": "bd-door", "role": "lock", "sceneName": "地址栏", "reason": "地址栏锁住，需要钥匙。" }
        ],
        "beats": [
          { "id": "b-term", "title": "输入密码", "action": "password", "uses": ["bd-term"], "requires": ["b-note", "b-bear"], "reveals": ["bd-key"], "product": "解密的情报", "expected": "246" },
          { "id": "b-door", "title": "用钥匙开地址栏", "action": "combine", "uses": ["bd-key", "bd-door"], "requires": ["b-term"], "resultOn": "bd-door", "consume": ["bd-key"], "product": "打开的地址栏" },
          { "id": "b-escape", "title": "离开收藏夹", "action": "deliver", "uses": ["result:b-door"], "requires": ["b-door"] }
        ]
      }
    ]
  },
  {
    "title": "深夜放映室 · 透明夏（内容接地示范）",
    "theme": "凌晨放映间——投影仪待机灯、幕布褶皱与磁带的塑料味",
    "adventureGrammar": "变形:指南写上卡带、卡带烧成引导,最终拼成一台能开机的放映仪",
    "creativeThesis": "每一份随手存下的投稿页，都是这台旧放映机缺失的一段引导。",
    "recurringMotif": "数据条（数据条上的数字、编号、刻度）",
    "surpriseTurn": "无",
    "premise": "素材是一则视频投稿页，它的网页描述里印着：视频播放量 1097、弹幕量 8、点赞数 53、投硬币枚数 15、收藏人数 119、转发人数 20；投稿编号 av4918172。你在凌晨的放映间醒来，投影仪待机，闸机锁着引导码——启动它的材料就藏在这些真实读数里。",
    "objective": "读卡带数据条，按指南写好引导卡，烧录进放映闸机，用播放数据拼出四位引导码，开机放映。",
    "targetMinutes": 10,
    "mechanics": ["闸机引导码 9715 = 播放量 1097 的末两位 97 + 投硬币枚数 15"],
    "hints": [
      "卡带侧面的数据条印着几个数字，看仔细。",
      "投稿指南压在数据条下面，挪开卡带才看得见。",
      "闸机要四位：播放量取末两位，再接上硬币数。"
    ],
    "scenes": [
      {
        "id": "fs-outer",
        "title": "放映外间",
        "description": "操作台上摊着卡带和指南，投影仪的待机灯一明一灭。",
        "focus": "待机的投影仪",
        "items": [
          { "id": "bk-tape", "role": "clue", "sceneName": "数据条卡带", "reason": "卡带侧的数据条印着：播放量 1097、弹幕量 8。条码下压着半张指南。", "digest": "B站视频《透明夏》的投稿页，播放数据齐全。", "sourceFacts": [{ "k": "播放量", "v": "1097" }, { "k": "弹幕量", "v": "8" }] },
          { "id": "bk-guide", "role": "tool", "sceneName": "投稿指南", "reason": "指南写着：投稿编号 av4918172 就是投影仪的引导前缀，但要写在一盘卡带上才生效。", "digest": "文档站的一页投稿指引，含投稿编号。", "sourceFacts": [{ "k": "稿件编号", "v": "av4918172" }], "hidden": true },
          { "id": "bk-blank", "role": "tool", "sceneName": "空白卡带", "reason": "一盘没写引导的空白卡带，标签还没贴。", "digest": "一盘待写的空白录像带。" }
        ],
        "beats": [
          { "id": "b1", "title": "读数据条", "action": "inspect", "uses": ["bk-tape"], "reveals": ["bk-guide"] },
          { "id": "b2", "title": "写引导卡", "action": "combine", "uses": ["bk-guide", "bk-blank"], "requires": ["b1"], "resultOn": "bk-blank", "product": "写好引导的卡带" }
        ]
      },
      {
        "id": "fs-inner",
        "title": "放映里间",
        "description": "里间立着连着投影仪的闸机，柜面上贴着放映员的留言。",
        "focus": "放映闸机",
        "items": [
          { "id": "bk-receipt", "role": "tool", "sceneName": "投稿回执", "reason": "投稿回执，编号一栏与指南对得上。回执背面：与引导卡一起插入闸机。", "digest": "一次投稿的回执存根。" },
          { "id": "bk-gate", "role": "lock", "sceneName": "放映闸机", "reason": "闸机缺四位引导码。面板刻着：播放量取末两位，接上投硬币枚数。", "digest": "B站投稿页的投币数据段。", "sourceFacts": [{ "k": "投硬币枚数", "v": "15" }] },
          { "id": "bk-screen", "role": "red_herring", "sceneName": "旧幕布", "reason": "卷起的幕布上只有去年夏天的放映日期，跟引导码无关。", "digest": "一块留着旧日期的幕布。", "hidden": true }
        ],
        "beats": [
          { "id": "b3", "title": "读投稿回执", "action": "inspect", "uses": ["bk-receipt"], "reveals": ["bk-screen"] },
          { "id": "b4", "title": "烧录引导", "action": "combine", "uses": ["result:b2", "bk-receipt"], "requires": ["b2"], "resultOn": "bk-receipt", "product": "烧录好的引导" },
          { "id": "b5", "title": "输入引导码", "action": "password", "uses": ["bk-gate"], "requires": ["b1", "b3"], "expected": "9715", "deriveFrom": ["bk-tape", "bk-gate"], "product": "解锁的闸机" },
          { "id": "b6", "title": "装入引导开机", "action": "combine", "uses": ["result:b4", "bk-gate"], "requires": ["b4", "b5"], "resultOn": "bk-gate", "product": "开始放映的投影仪" },
          { "id": "b7", "title": "落幕离场", "action": "deliver", "uses": ["result:b6"], "requires": ["b6"] }
        ]
      }
    ]
  }
];
