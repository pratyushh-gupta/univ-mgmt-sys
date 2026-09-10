const teachingCourses = [
  { code: "CS401", name: "Operating Systems", department: "Computer Science", students: 42 },
  { code: "CS407", name: "Advanced OS Lab", department: "Computer Science", students: 30 },
];

export default function MyCourses() {
  return (
    <section className="panel full">
      <div className="panel-title">
        <h2>My Courses</h2>
      </div>

      <div className="table">
        <div className="table-head">
          <span>Code</span>
          <span>Course Name</span>
          <span>Department</span>
          <span>Students</span>
        </div>

        {teachingCourses.map((c) => (
          <div className="table-row" key={c.code}>
            <span>{c.code}</span>
            <strong>{c.name}</strong>
            <span>{c.department}</span>
            <span>{c.students}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
