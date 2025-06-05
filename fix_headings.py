import re
import argparse
import os

def adjust_markdown_headings(input_filepath, output_filepath):
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f_in:
            lines = f_in.readlines()
    except FileNotFoundError:
        print(f"错误：输入文件 '{input_filepath}' 未找到。")
        return
    except Exception as e:
        print(f"读取输入文件 '{input_filepath}' 时出错: {e}")
        return

    main_title_keyword = "AI+Education行业洞察"
    references_keyword = "参考资料"
    
    # First pass: adjust heading levels and collect processed headings
    processed_lines = []
    processed_headings = []  # Store (line_index, level, text) after processing
    in_references_section = False

    for i, line_content in enumerate(lines):
        stripped_line = line_content.strip()

        # Preserve empty lines
        if not stripped_line:
            processed_lines.append(line_content)
            continue

        # Handle the "参考资料" section - keep everything unchanged
        if references_keyword in stripped_line and stripped_line.startswith("#"):
            in_references_section = True
            processed_lines.append(line_content)
            continue
        
        if in_references_section:
            processed_lines.append(line_content)
            continue

        # Process headings based on original structure
        heading_match = re.match(r"^(#+)\s*(.*)", stripped_line)
        if heading_match:
            original_level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            if not heading_text:
                processed_lines.append(line_content)
                continue

            # Determine the appropriate heading level
            if main_title_keyword in heading_text:
                new_level = 1
                formatted_line = f"# {heading_text}\n"
            elif re.match(r"第[一二三四五六七八九十]+部分[:：]", heading_text):
                new_level = 2
                formatted_line = f"## {heading_text}\n"
            else:
                # Adjust levels: H1->H2, H2->H3, H3->H4, H4+->H5
                if original_level == 1:
                    new_level = 2
                    formatted_line = f"## {heading_text}\n"
                elif original_level == 2:
                    new_level = 3
                    formatted_line = f"### {heading_text}\n"
                elif original_level == 3:
                    new_level = 4
                    formatted_line = f"#### {heading_text}\n"
                elif original_level >= 4:
                    new_level = 5
                    formatted_line = f"##### {heading_text}\n"

            processed_lines.append(formatted_line)
            processed_headings.append((len(processed_lines) - 1, new_level, heading_text))
        else:
            # Not a heading line
            processed_lines.append(line_content)

    # Second pass: remove headings that immediately precede H2 headings
    lines_to_skip = set()
    special_sections = ["章节概述", "章节总结"]

    # Look for any heading followed by H2 heading
    for i in range(len(processed_headings) - 1):
        current_line_idx, current_level, current_text = processed_headings[i]
        next_line_idx, next_level, next_text = processed_headings[i + 1]
        
        # Skip special sections
        if current_text in special_sections:
            continue
            
        # Skip main title and "第X部分" titles
        if main_title_keyword in current_text or re.match(r"第[一二三四五六七八九十]+部分[:：]", current_text):
            continue
        
        # If next heading is H2, remove current heading
        if next_level == 2:
            lines_to_skip.add(current_line_idx)
            print(f"删除H2前的标题: '{current_text}' (H2标题: '{next_text}')")

    # Third pass: generate final output without skipped lines
    final_lines = []
    for i, line in enumerate(processed_lines):
        if i not in lines_to_skip:
            final_lines.append(line)

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f_out:
            f_out.writelines(final_lines)
        print(f"处理成功。输出已写入 '{output_filepath}'")
        print(f"共删除了 {len(lines_to_skip)} 个H2前的标题")
    except Exception as e:
        print(f"写入输出文件 '{output_filepath}' 时出错: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="调整Markdown报告中的标题级别。")
    parser.add_argument("input_file", help="输入Markdown文件的路径。")
    parser.add_argument("-o", "--output_file", 
                        help="输出Markdown文件的路径。如果未提供，则默认为在原始文件名后附加'_processed'。")
    
    args = parser.parse_args()

    output_filename = args.output_file
    if not output_filename:
        base, ext = os.path.splitext(args.input_file)
        output_filename = f"{base}_processed{ext}"
        
    adjust_markdown_headings(args.input_file, output_filename) 