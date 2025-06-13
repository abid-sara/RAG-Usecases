import { motion } from "framer-motion";
import logoImage from "../../assets/images/logo.png"; // Import the image

export const Overview = () => {
  return (
    <>
      <motion.div
        key="overview"
        className="max-w-3xl mx-auto md:mt-20"
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.98 }}
        transition={{ delay: 0.75 }}
      >
        <div className="rounded-xl p-6 flex flex-col gap-8 leading-relaxed text-center max-w-xl  discussion-box">
          <div className="flex justify-center ">
            <img
              src={logoImage}
              alt="Logo"
              className="h-24 sm:h-32 md:h-36 lg:h-44 w-auto mx-auto"
            />
          </div>
          <p id="logo-text" className="rtl-text" dir="rtl">
            <strong>وزارة التعليم العالي و البحث العلمي</strong>
          </p>
          <p className="rtl-text" dir="rtl">
            <strong> مرحبًا بكم في نظام محادثة الذكاء الاصطناعي! </strong>
            <br />
            تم تصميم هذا النظام لتوفير استفسارات موثوقة وسلسة حول الوثائق
            التنظيمية لوزارة التعليم العالي.
            <br />
            نقدم لكم إجابات دقيقة مما يتيح لكم الوصول إلى المعلومات بسهولة
            وسرعة.
            <br />
            <strong>معًا نحو تجربة رقمية مبتكرة!</strong>
          </p>
        </div>
      </motion.div>
    </>
  );
};
