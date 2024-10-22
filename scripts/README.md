## 代码说明：
1. 正则表达式：我们通过正则表达式从每个项目笔记中提取项目名称、Finding 编号、Finding 标题、严重性、类别等信息。
2. 内部链接生成：通过使用 Obsidian 的 [[project_name#finding_number]] 链接格式，将笔记中的 Finding 直接链接到全局索引。
3. 分类和优先级：代码按照优先级（High, Medium）和类别（Category）对所有的 findings 进行分类，并分别在全局索引中展示。
4. 索引生成：最终结果会写入一个全局索引文件 Global_Audit_Index.md，可以直接在 Obsidian 中查看并点击跳转。
## 如何使用：
1. 在你的 Obsidian 笔记系统中创建一个文件夹（如 audit_notes），存放所有项目的审计笔记文件。
2. 在代码中修改 project_notes_dir 和 global_index_file 路径，指向你的笔记文件夹和全局索引保存路径。
3. 运行代码后，生成的 Global_Audit_Index.md 文件就可以在 Obsidian 中作为全局索引来使用了。
## 后续改进：
- 可以增加更多的细节提取，例如 Impact、PoC 等字段。
- 如果 Obsidian 未来需要的索引格式或需求有变，可以轻松调整代码结构。
