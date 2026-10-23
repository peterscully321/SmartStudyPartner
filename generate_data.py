import pandas as pd
import random
from pathlib import Path


def generate_dataset(num_records=800, seed=42, output_path=None):
    rng = random.Random(seed)
    categories = [
        "Data Science", "Machine Learning", "Web Development", "Cloud Computing",
        "Algorithms & Data Structures", "Databases", "Mobile App Development",
        "Cybersecurity", "DevOps", "UI/UX Design", "Software Engineering", "Networking"
    ]
    
    # Keyword pools for generating realistic titles and descriptions
    keywords = {
        "Data Science": ["Pandas", "NumPy", "Data Analysis", "Visualization", "Statistics", "Data Cleaning", "Matplotlib", "Seaborn", "Data Wrangling", "Big Data", "EDA"],
        "Machine Learning": ["Scikit-learn", "TensorFlow", "PyTorch", "Deep Learning", "Neural Networks", "Classification", "Regression", "NLP", "Computer Vision", "Model Deployment", "Reinforcement Learning"],
        "Web Development": ["HTML", "CSS", "JavaScript", "React", "Node.js", "Express", "Frontend", "Backend", "Full-Stack", "Django", "Flask", "Vue", "Angular"],
        "Cloud Computing": ["AWS", "Azure", "Google Cloud", "EC2", "S3", "Cloud Architecture", "Serverless", "Lambda", "Docker", "Kubernetes", "IaaS", "PaaS"],
        "Algorithms & Data Structures": ["Sorting", "Graph Theory", "Dynamic Programming", "Trees", "Hash Tables", "Linked Lists", "Big O Notation", "Recursion", "Greedy Algorithms", "LeetCode", "Binary Search"],
        "Databases": ["SQL", "MySQL", "PostgreSQL", "MongoDB", "NoSQL", "Redis", "Database Design", "Normalization", "Query Optimization", "ACID", "Cassandra"],
        "Mobile App Development": ["Android", "iOS", "Flutter", "React Native", "Swift", "Kotlin", "Mobile UI", "App Deployment", "Cross-Platform", "State Management", "Mobile APIs"],
        "Cybersecurity": ["Penetration Testing", "Cryptography", "Ethical Hacking", "Network Security", "Malware Analysis", "OWASP", "Vulnerability Assessment", "Firewalls", "Incident Response", "Security Auditing"],
        "DevOps": ["CI/CD", "Jenkins", "GitLab CI", "Terraform", "Ansible", "Infrastructure as Code", "Monitoring", "Prometheus", "Grafana", "Linux Administration", "Agile"],
        "UI/UX Design": ["Figma", "User Research", "Wireframing", "Prototyping", "Design Systems", "Usability Testing", "Adobe XD", "Accessibility", "Interaction Design", "User Personas"],
        "Software Engineering": ["Design Patterns", "SOLID Principles", "Agile", "Scrum", "TDD", "Version Control", "Git", "Software Architecture", "Microservices", "Code Review"],
        "Networking": ["TCP/IP", "DNS", "HTTP/HTTPS", "Routing", "Switching", "Subnetting", "OSI Model", "Network Troubleshooting", "BGP", "VLANs", "Wireshark"]
    }

    formats = ["Tutorial", "Course", "Article", "Video", "Documentation", "Book", "Cheat Sheet", "Project Guide", "Workshop", "Case Study"]
    levels = ["Beginner", "Intermediate", "Advanced"]

    data = []
    
    for i in range(1, num_records + 1):
        category = rng.choice(categories)
        cat_keywords = keywords[category]
        
        # Select 2-4 keywords for the title
        selected_keywords = rng.sample(cat_keywords, rng.randint(2, min(4, len(cat_keywords))))
        
        # Select format and level
        resource_format = rng.choice(formats)
        level = rng.choice(levels)
        
        # Generate Title
        title_templates = [
            f"Mastering {' and '.join(selected_keywords[:2])} for {level}s",
            f"The Ultimate {resource_format} to {selected_keywords[0]}",
            f"A Practical Guide to {' and '.join(selected_keywords)}",
            f"Introduction to {selected_keywords[0]}: A {level} {resource_format}",
            f"Advanced Techniques in {selected_keywords[0]} and {selected_keywords[1]}",
            f"Learn {category} by building projects with {selected_keywords[0]}"
        ]
        title = rng.choice(title_templates)
        
        # Generate Description
        desc_templates = [
            f"This comprehensive {resource_format.lower()} covers the fundamentals and advanced concepts of {selected_keywords[0]}. Perfect for {level.lower()} learners looking to improve their {category} skills.",
            f"Dive deep into {', '.join(selected_keywords)} with this hands-on guide. You will learn how to apply these concepts in real-world {category} scenarios.",
            f"Explore the world of {category} through the lens of {selected_keywords[0]}. This material is tailored for a {level.lower()} audience and includes practical examples.",
            f"An essential resource for anyone studying {category}. We focus heavily on {selected_keywords[0]} and {selected_keywords[1]} to give you a solid foundation."
        ]
        description = rng.choice(desc_templates)
        
        # Generate Tags
        tags = ", ".join(selected_keywords + [category, level, resource_format])
        
        data.append({
            "Resource_ID": f"RES_{i:04d}",
            "Title": title,
            "Category": category,
            "Description": description,
            "Level": level,
            "Format": resource_format,
            "Tags": tags
        })
        
    df = pd.DataFrame(data)
    
    destination = Path(output_path) if output_path else Path(__file__).with_name("study_resources.csv")
    if not destination.is_absolute():
        destination = Path(__file__).resolve().parent / destination
    df.to_csv(destination, index=False)
    print(f"Generated {len(df)} sample resources in '{destination}'.")

if __name__ == "__main__":
    generate_dataset(800)
