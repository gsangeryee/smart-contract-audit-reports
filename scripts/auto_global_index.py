import os
import re

# 设置审计项目笔记的文件夹路径
project_notes_dir = './audit_notes'
# 设置生成的全局索引文件路径
global_index_file = './Global_Audit_Index.md'

# 定义正则表达式匹配审计项目笔记中的关键信息
project_name_pattern = re.compile(r"# Audit Project: (.+)")
finding_pattern = re.compile(r"### Finding (\d+): (.+) \[(.+)\] \[Category: (.+)\]")

# 存储索引信息
findings_by_priority = {"High": [], "Medium": []}
findings_by_category = {}

# 遍历审计项目笔记文件夹中的所有 markdown 文件
for filename in os.listdir(project_notes_dir):
    if filename.endswith(".md"):
        filepath = os.path.join(project_notes_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

            # 提取项目名称
            project_name_match = project_name_pattern.search(content)
            if project_name_match:
                project_name = project_name_match.group(1)

            # 提取所有的 finding 信息
            findings = finding_pattern.findall(content)
            for finding in findings:
                finding_number, finding_title, severity, category = finding

                # 生成内部链接
                finding_link = f"[[{project_name}#Finding-{finding_number}]]: {finding_title}"

                # 按优先级分类
                if severity in findings_by_priority:
                    findings_by_priority[severity].append(finding_link)

                # 按类别分类
                if category not in findings_by_category:
                    findings_by_category[category] = []
                findings_by_category[category].append(finding_link)

# 生成全局索引内容
index_content = "# Global Audit Index\n\n## By Priority\n\n"
for severity, findings in findings_by_priority.items():
    index_content += f"### {severity} Severity Findings\n"
    for finding in findings:
        index_content += f"- {finding}\n"
    index_content += "\n"

index_content += "## By Category\n\n"
for category, findings in findings_by_category.items():
    index_content += f"### {category}\n"
    for finding in findings:
        index_content += f"- {finding}\n"
    index_content += "\n"

# 将索引内容写入全局索引文件
with open(global_index_file, 'w', encoding='utf-8') as index_file:
    index_file.write(index_content)

print("Global audit index has been generated.")
